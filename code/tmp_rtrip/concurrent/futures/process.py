"""Implements ProcessPoolExecutor.

The follow diagram and text describe the data-flow through the system:

|======================= In-process =====================|== Out-of-process ==|

+----------+     +----------+       +--------+     +-----------+    +---------+
|          |  => | Work Ids |    => |        |  => | Call Q    | => |         |
|          |     +----------+       |        |     +-----------+    |         |
|          |     | ...      |       |        |     | ...       |    |         |
|          |     | 6        |       |        |     | 5, call() |    |         |
|          |     | 7        |       |        |     | ...       |    |         |
| Process  |     | ...      |       | Local  |     +-----------+    | Process |
|  Pool    |     +----------+       | Worker |                      |  #1..n  |
| Executor |                        | Thread |                      |         |
|          |     +----------- +     |        |     +-----------+    |         |
|          | <=> | Work Items | <=> |        | <=  | Result Q  | <= |         |
|          |     +------------+     |        |     +-----------+    |         |
|          |     | 6: call()  |     |        |     | ...       |    |         |
|          |     |    future  |     |        |     | 4, result |    |         |
|          |     | ...        |     |        |     | 3, except |    |         |
+----------+     +------------+     +--------+     +-----------+    +---------+

Executor.submit() called:
- creates a uniquely numbered _WorkItem and adds it to the "Work Items" dict
- adds the id of the _WorkItem to the "Work Ids" queue

Local worker thread:
- reads work ids from the "Work Ids" queue and looks up the corresponding
  WorkItem from the "Work Items" dict: if the work item has been cancelled then
  it is simply removed from the dict, otherwise it is repackaged as a
  _CallItem and put in the "Call Q". New _CallItems are put in the "Call Q"
  until "Call Q" is full. NOTE: the size of the "Call Q" is kept small because
  calls placed in the "Call Q" can no longer be cancelled with Future.cancel().
- reads _ResultItems from "Result Q", updates the future stored in the
  "Work Items" dict and deletes the dict entry

Process #1..n:
- reads _CallItems from "Call Q", executes the calls, and puts the resulting
  _ResultItems in "Result Q\"
"""
__author__ = 'Brian Quinlan (brian@sweetapp.com)'
import atexit
import os
from concurrent.futures import _base
import queue
from queue import Full
import multiprocessing
from multiprocessing import SimpleQueue
from multiprocessing.connection import wait
import threading
import weakref
from functools import partial
import itertools
import traceback
_threads_queues = weakref.WeakKeyDictionary()
_shutdown = False


def _python_exit():
    global _shutdown
    _shutdown = True
    items = list(_threads_queues.items())
    for t, q in items:
        q.put(None)
    for t, q in items:
        t.join()


EXTRA_QUEUED_CALLS = 1


class _RemoteTraceback(Exception):

    def __init__(self, tb):
        self.tb = tb

    def __str__(self):
        return self.tb


class _ExceptionWithTraceback:

    def __init__(self, exc, tb):
        tb = traceback.format_exception(type(exc), exc, tb)
        tb = ''.join(tb)
        self.exc = exc
        self.tb = '\n"""\n%s"""' % tb

    def __reduce__(self):
        return _rebuild_exc, (self.exc, self.tb)


def _rebuild_exc(exc, tb):
    exc.__cause__ = _RemoteTraceback(tb)
    return exc


class _WorkItem(object):

    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class _ResultItem(object):

    def __init__(self, work_id, exception=None, result=None):
        self.work_id = work_id
        self.exception = exception
        self.result = result


class _CallItem(object):

    def __init__(self, work_id, fn, args, kwargs):
        self.work_id = work_id
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


def _get_chunks(*iterables, chunksize):
    """ Iterates over zip()ed iterables in chunks. """
    it = zip(*iterables)
    while True:
        chunk = tuple(itertools.islice(it, chunksize))
        if not chunk:
            return
        yield chunk


def _process_chunk(fn, chunk):
    """ Processes a chunk of an iterable passed to map.

    Runs the function passed to map() on a chunk of the
    iterable passed to map.

    This function is run in a separate process.

    """
    return [fn(*args) for args in chunk]


def _process_worker(call_queue, result_queue):
    """Evaluates calls from call_queue and places the results in result_queue.

    This worker is run in a separate process.

    Args:
        call_queue: A multiprocessing.Queue of _CallItems that will be read and
            evaluated by the worker.
        result_queue: A multiprocessing.Queue of _ResultItems that will written
            to by the worker.
        shutdown: A multiprocessing.Event that will be set as a signal to the
            worker that it should exit when call_queue is empty.
    """
    while True:
        call_item = call_queue.get(block=True)
        if call_item is None:
            result_queue.put(os.getpid())
            return
        try:
            r = call_item.fn(*call_item.args, **call_item.kwargs)
        except BaseException as e:
            exc = _ExceptionWithTraceback(e, e.__traceback__)
            result_queue.put(_ResultItem(call_item.work_id, exception=exc))
        else:
            result_queue.put(_ResultItem(call_item.work_id, result=r))


def _add_call_item_to_queue(pending_work_items, work_ids, call_queue):
    """Fills call_queue with _WorkItems from pending_work_items.

    This function never blocks.

    Args:
        pending_work_items: A dict mapping work ids to _WorkItems e.g.
            {5: <_WorkItem...>, 6: <_WorkItem...>, ...}
        work_ids: A queue.Queue of work ids e.g. Queue([5, 6, ...]). Work ids
            are consumed and the corresponding _WorkItems from
            pending_work_items are transformed into _CallItems and put in
            call_queue.
        call_queue: A multiprocessing.Queue that will be filled with _CallItems
            derived from _WorkItems.
    """
    while True:
        if call_queue.full():
            return
        try:
            work_id = work_ids.get(block=False)
        except queue.Empty:
            return
        else:
            work_item = pending_work_items[work_id]
            if work_item.future.set_running_or_notify_cancel():
                call_queue.put(_CallItem(work_id, work_item.fn, work_item.
                    args, work_item.kwargs), block=True)
            else:
                del pending_work_items[work_id]
                continue


def _queue_management_worker(executor_reference, processes,
    pending_work_items, work_ids_queue, call_queue, result_queue):
    """Manages the communication between this process and the worker processes.

    This function is run in a local thread.

    Args:
        executor_reference: A weakref.ref to the ProcessPoolExecutor that owns
            this thread. Used to determine if the ProcessPoolExecutor has been
            garbage collected and that this function can exit.
        process: A list of the multiprocessing.Process instances used as
            workers.
        pending_work_items: A dict mapping work ids to _WorkItems e.g.
            {5: <_WorkItem...>, 6: <_WorkItem...>, ...}
        work_ids_queue: A queue.Queue of work ids e.g. Queue([5, 6, ...]).
        call_queue: A multiprocessing.Queue that will be filled with _CallItems
            derived from _WorkItems for processing by the process workers.
        result_queue: A multiprocessing.Queue of _ResultItems generated by the
            process workers.
    """
    executor = None

    def shutting_down():
        return _shutdown or executor is None or executor._shutdown_thread

    def shutdown_worker():
        nb_children_alive = sum(p.is_alive() for p in processes.values())
        for i in range(0, nb_children_alive):
            call_queue.put_nowait(None)
        call_queue.close()
        for p in processes.values():
            p.join()
    reader = result_queue._reader
    while True:
        _add_call_item_to_queue(pending_work_items, work_ids_queue, call_queue)
        sentinels = [p.sentinel for p in processes.values()]
        assert sentinels
        ready = wait([reader] + sentinels)
        if reader in ready:
            result_item = reader.recv()
        else:
            executor = executor_reference()
            if executor is not None:
                executor._broken = True
                executor._shutdown_thread = True
                executor = None
            for work_id, work_item in pending_work_items.items():
                work_item.future.set_exception(BrokenProcessPool(
                    'A process in the process pool was terminated abruptly while the future was running or pending.'
                    ))
                del work_item
            pending_work_items.clear()
            for p in processes.values():
                p.terminate()
            shutdown_worker()
            return
        if isinstance(result_item, int):
            assert shutting_down()
            p = processes.pop(result_item)
            p.join()
            if not processes:
                shutdown_worker()
                return
        elif result_item is not None:
            work_item = pending_work_items.pop(result_item.work_id, None)
            if work_item is not None:
                if result_item.exception:
                    work_item.future.set_exception(result_item.exception)
                else:
                    work_item.future.set_result(result_item.result)
                del work_item
        executor = executor_reference()
        if shutting_down():
            try:
                if not pending_work_items:
                    shutdown_worker()
                    return
            except Full:
                pass
        executor = None


_system_limits_checked = False
_system_limited = None


def _check_system_limits():
    global _system_limits_checked, _system_limited
    if _system_limits_checked:
        if _system_limited:
            raise NotImplementedError(_system_limited)
    _system_limits_checked = True
    try:
        nsems_max = os.sysconf('SC_SEM_NSEMS_MAX')
    except (AttributeError, ValueError):
        return
    if nsems_max == -1:
        return
    if nsems_max >= 256:
        return
    _system_limited = (
        'system provides too few semaphores (%d available, 256 necessary)' %
        nsems_max)
    raise NotImplementedError(_system_limited)


class BrokenProcessPool(RuntimeError):
    """
    Raised when a process in a ProcessPoolExecutor terminated abruptly
    while a future was in the running state.
    """


class ProcessPoolExecutor(_base.Executor):

    def __init__(self, max_workers=None):
        """Initializes a new ProcessPoolExecutor instance.

        Args:
            max_workers: The maximum number of processes that can be used to
                execute the given calls. If None or not given then as many
                worker processes will be created as the machine has processors.
        """
        _check_system_limits()
        if max_workers is None:
            self._max_workers = os.cpu_count() or 1
        else:
            if max_workers <= 0:
                raise ValueError('max_workers must be greater than 0')
            self._max_workers = max_workers
        self._call_queue = multiprocessing.Queue(self._max_workers +
            EXTRA_QUEUED_CALLS)
        self._call_queue._ignore_epipe = True
        self._result_queue = SimpleQueue()
        self._work_ids = queue.Queue()
        self._queue_management_thread = None
        self._processes = {}
        self._shutdown_thread = False
        self._shutdown_lock = threading.Lock()
        self._broken = False
        self._queue_count = 0
        self._pending_work_items = {}

    def _start_queue_management_thread(self):

        def weakref_cb(_, q=self._result_queue):
            q.put(None)
        if self._queue_management_thread is None:
            self._adjust_process_count()
            self._queue_management_thread = threading.Thread(target=
                _queue_management_worker, args=(weakref.ref(self,
                weakref_cb), self._processes, self._pending_work_items,
                self._work_ids, self._call_queue, self._result_queue))
            self._queue_management_thread.daemon = True
            self._queue_management_thread.start()
            _threads_queues[self._queue_management_thread] = self._result_queue

    def _adjust_process_count(self):
        for _ in range(len(self._processes), self._max_workers):
            p = multiprocessing.Process(target=_process_worker, args=(self.
                _call_queue, self._result_queue))
            p.start()
            self._processes[p.pid] = p

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._broken:
                raise BrokenProcessPool(
                    'A child process terminated abruptly, the process pool is not usable anymore'
                    )
            if self._shutdown_thread:
                raise RuntimeError('cannot schedule new futures after shutdown'
                    )
            f = _base.Future()
            w = _WorkItem(f, fn, args, kwargs)
            self._pending_work_items[self._queue_count] = w
            self._work_ids.put(self._queue_count)
            self._queue_count += 1
            self._result_queue.put(None)
            self._start_queue_management_thread()
            return f
    submit.__doc__ = _base.Executor.submit.__doc__

    def map(self, fn, *iterables, timeout=None, chunksize=1):
        """Returns an iterator equivalent to map(fn, iter).

        Args:
            fn: A callable that will take as many arguments as there are
                passed iterables.
            timeout: The maximum number of seconds to wait. If None, then there
                is no limit on the wait time.
            chunksize: If greater than one, the iterables will be chopped into
                chunks of size chunksize and submitted to the process pool.
                If set to one, the items in the list will be sent one at a time.

        Returns:
            An iterator equivalent to: map(func, *iterables) but the calls may
            be evaluated out-of-order.

        Raises:
            TimeoutError: If the entire result iterator could not be generated
                before the given timeout.
            Exception: If fn(*args) raises for any values.
        """
        if chunksize < 1:
            raise ValueError('chunksize must be >= 1.')
        results = super().map(partial(_process_chunk, fn), _get_chunks(*
            iterables, chunksize=chunksize), timeout=timeout)
        return itertools.chain.from_iterable(results)

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown_thread = True
        if self._queue_management_thread:
            self._result_queue.put(None)
            if wait:
                self._queue_management_thread.join()
        self._queue_management_thread = None
        self._call_queue = None
        self._result_queue = None
        self._processes = None
    shutdown.__doc__ = _base.Executor.shutdown.__doc__


atexit.register(_python_exit)
