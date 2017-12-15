"""Selector and proactor event loops for Windows."""
import _winapi
import errno
import math
import socket
import struct
import weakref
from . import events
from . import base_subprocess
from . import futures
from . import proactor_events
from . import selector_events
from . import tasks
from . import windows_utils
from . import _overlapped
from .coroutines import coroutine
from .log import logger
__all__ = ['SelectorEventLoop', 'ProactorEventLoop', 'IocpProactor',
    'DefaultEventLoopPolicy']
NULL = 0
INFINITE = 4294967295
ERROR_CONNECTION_REFUSED = 1225
ERROR_CONNECTION_ABORTED = 1236
CONNECT_PIPE_INIT_DELAY = 0.001
CONNECT_PIPE_MAX_DELAY = 0.1


class _OverlappedFuture(futures.Future):
    """Subclass of Future which represents an overlapped operation.

    Cancelling it will immediately cancel the overlapped operation.
    """

    def __init__(self, ov, *, loop=None):
        super().__init__(loop=loop)
        if self._source_traceback:
            del self._source_traceback[-1]
        self._ov = ov

    def _repr_info(self):
        info = super()._repr_info()
        if self._ov is not None:
            state = 'pending' if self._ov.pending else 'completed'
            info.insert(1, 'overlapped=<%s, %#x>' % (state, self._ov.address))
        return info

    def _cancel_overlapped(self):
        if self._ov is None:
            return
        try:
            self._ov.cancel()
        except OSError as exc:
            context = {'message': 'Cancelling an overlapped future failed',
                'exception': exc, 'future': self}
            if self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
        self._ov = None

    def cancel(self):
        self._cancel_overlapped()
        return super().cancel()

    def set_exception(self, exception):
        super().set_exception(exception)
        self._cancel_overlapped()

    def set_result(self, result):
        super().set_result(result)
        self._ov = None


class _BaseWaitHandleFuture(futures.Future):
    """Subclass of Future which represents a wait handle."""

    def __init__(self, ov, handle, wait_handle, *, loop=None):
        super().__init__(loop=loop)
        if self._source_traceback:
            del self._source_traceback[-1]
        self._ov = ov
        self._handle = handle
        self._wait_handle = wait_handle
        self._registered = True

    def _poll(self):
        return _winapi.WaitForSingleObject(self._handle, 0
            ) == _winapi.WAIT_OBJECT_0

    def _repr_info(self):
        info = super()._repr_info()
        info.append('handle=%#x' % self._handle)
        if self._handle is not None:
            state = 'signaled' if self._poll() else 'waiting'
            info.append(state)
        if self._wait_handle is not None:
            info.append('wait_handle=%#x' % self._wait_handle)
        return info

    def _unregister_wait_cb(self, fut):
        self._ov = None

    def _unregister_wait(self):
        if not self._registered:
            return
        self._registered = False
        wait_handle = self._wait_handle
        self._wait_handle = None
        try:
            _overlapped.UnregisterWait(wait_handle)
        except OSError as exc:
            if exc.winerror != _overlapped.ERROR_IO_PENDING:
                context = {'message':
                    'Failed to unregister the wait handle', 'exception':
                    exc, 'future': self}
                if self._source_traceback:
                    context['source_traceback'] = self._source_traceback
                self._loop.call_exception_handler(context)
                return
        self._unregister_wait_cb(None)

    def cancel(self):
        self._unregister_wait()
        return super().cancel()

    def set_exception(self, exception):
        self._unregister_wait()
        super().set_exception(exception)

    def set_result(self, result):
        self._unregister_wait()
        super().set_result(result)


class _WaitCancelFuture(_BaseWaitHandleFuture):
    """Subclass of Future which represents a wait for the cancellation of a
    _WaitHandleFuture using an event.
    """

    def __init__(self, ov, event, wait_handle, *, loop=None):
        super().__init__(ov, event, wait_handle, loop=loop)
        self._done_callback = None

    def cancel(self):
        raise RuntimeError('_WaitCancelFuture must not be cancelled')

    def set_result(self, result):
        super().set_result(result)
        if self._done_callback is not None:
            self._done_callback(self)

    def set_exception(self, exception):
        super().set_exception(exception)
        if self._done_callback is not None:
            self._done_callback(self)


class _WaitHandleFuture(_BaseWaitHandleFuture):

    def __init__(self, ov, handle, wait_handle, proactor, *, loop=None):
        super().__init__(ov, handle, wait_handle, loop=loop)
        self._proactor = proactor
        self._unregister_proactor = True
        self._event = _overlapped.CreateEvent(None, True, False, None)
        self._event_fut = None

    def _unregister_wait_cb(self, fut):
        if self._event is not None:
            _winapi.CloseHandle(self._event)
            self._event = None
            self._event_fut = None
        self._proactor._unregister(self._ov)
        self._proactor = None
        super()._unregister_wait_cb(fut)

    def _unregister_wait(self):
        if not self._registered:
            return
        self._registered = False
        wait_handle = self._wait_handle
        self._wait_handle = None
        try:
            _overlapped.UnregisterWaitEx(wait_handle, self._event)
        except OSError as exc:
            if exc.winerror != _overlapped.ERROR_IO_PENDING:
                context = {'message':
                    'Failed to unregister the wait handle', 'exception':
                    exc, 'future': self}
                if self._source_traceback:
                    context['source_traceback'] = self._source_traceback
                self._loop.call_exception_handler(context)
                return
        self._event_fut = self._proactor._wait_cancel(self._event, self.
            _unregister_wait_cb)


class PipeServer(object):
    """Class representing a pipe server.

    This is much like a bound, listening socket.
    """

    def __init__(self, address):
        self._address = address
        self._free_instances = weakref.WeakSet()
        self._pipe = None
        self._accept_pipe_future = None
        self._pipe = self._server_pipe_handle(True)

    def _get_unconnected_pipe(self):
        tmp, self._pipe = self._pipe, self._server_pipe_handle(False)
        return tmp

    def _server_pipe_handle(self, first):
        if self.closed():
            return None
        flags = _winapi.PIPE_ACCESS_DUPLEX | _winapi.FILE_FLAG_OVERLAPPED
        if first:
            flags |= _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE
        h = _winapi.CreateNamedPipe(self._address, flags, _winapi.
            PIPE_TYPE_MESSAGE | _winapi.PIPE_READMODE_MESSAGE | _winapi.
            PIPE_WAIT, _winapi.PIPE_UNLIMITED_INSTANCES, windows_utils.
            BUFSIZE, windows_utils.BUFSIZE, _winapi.NMPWAIT_WAIT_FOREVER,
            _winapi.NULL)
        pipe = windows_utils.PipeHandle(h)
        self._free_instances.add(pipe)
        return pipe

    def closed(self):
        return self._address is None

    def close(self):
        if self._accept_pipe_future is not None:
            self._accept_pipe_future.cancel()
            self._accept_pipe_future = None
        if self._address is not None:
            for pipe in self._free_instances:
                pipe.close()
            self._pipe = None
            self._address = None
            self._free_instances.clear()
    __del__ = close


class _WindowsSelectorEventLoop(selector_events.BaseSelectorEventLoop):
    """Windows version of selector event loop."""

    def _socketpair(self):
        return windows_utils.socketpair()


class ProactorEventLoop(proactor_events.BaseProactorEventLoop):
    """Windows version of proactor event loop using IOCP."""

    def __init__(self, proactor=None):
        if proactor is None:
            proactor = IocpProactor()
        super().__init__(proactor)

    def _socketpair(self):
        return windows_utils.socketpair()

    @coroutine
    def create_pipe_connection(self, protocol_factory, address):
        f = self._proactor.connect_pipe(address)
        pipe = yield from f
        protocol = protocol_factory()
        trans = self._make_duplex_pipe_transport(pipe, protocol, extra={
            'addr': address})
        return trans, protocol

    @coroutine
    def start_serving_pipe(self, protocol_factory, address):
        server = PipeServer(address)

        def loop_accept_pipe(f=None):
            pipe = None
            try:
                if f:
                    pipe = f.result()
                    server._free_instances.discard(pipe)
                    if server.closed():
                        pipe.close()
                        return
                    protocol = protocol_factory()
                    self._make_duplex_pipe_transport(pipe, protocol, extra=
                        {'addr': address})
                pipe = server._get_unconnected_pipe()
                if pipe is None:
                    return
                f = self._proactor.accept_pipe(pipe)
            except OSError as exc:
                if pipe and pipe.fileno() != -1:
                    self.call_exception_handler({'message':
                        'Pipe accept failed', 'exception': exc, 'pipe': pipe})
                    pipe.close()
                elif self._debug:
                    logger.warning('Accept pipe failed on pipe %r', pipe,
                        exc_info=True)
            except futures.CancelledError:
                if pipe:
                    pipe.close()
            else:
                server._accept_pipe_future = f
                f.add_done_callback(loop_accept_pipe)
        self.call_soon(loop_accept_pipe)
        return [server]

    @coroutine
    def _make_subprocess_transport(self, protocol, args, shell, stdin,
        stdout, stderr, bufsize, extra=None, **kwargs):
        waiter = self.create_future()
        transp = _WindowsSubprocessTransport(self, protocol, args, shell,
            stdin, stdout, stderr, bufsize, waiter=waiter, extra=extra, **
            kwargs)
        try:
            yield from waiter
        except Exception as exc:
            err = exc
        else:
            err = None
        if err is not None:
            transp.close()
            yield from transp._wait()
            raise err
        return transp


class IocpProactor:
    """Proactor implementation using IOCP."""

    def __init__(self, concurrency=4294967295):
        self._loop = None
        self._results = []
        self._iocp = _overlapped.CreateIoCompletionPort(_overlapped.
            INVALID_HANDLE_VALUE, NULL, 0, concurrency)
        self._cache = {}
        self._registered = weakref.WeakSet()
        self._unregistered = []
        self._stopped_serving = weakref.WeakSet()

    def __repr__(self):
        return '<%s overlapped#=%s result#=%s>' % (self.__class__.__name__,
            len(self._cache), len(self._results))

    def set_loop(self, loop):
        self._loop = loop

    def select(self, timeout=None):
        if not self._results:
            self._poll(timeout)
        tmp = self._results
        self._results = []
        return tmp

    def _result(self, value):
        fut = self._loop.create_future()
        fut.set_result(value)
        return fut

    def recv(self, conn, nbytes, flags=0):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)
        try:
            if isinstance(conn, socket.socket):
                ov.WSARecv(conn.fileno(), nbytes, flags)
            else:
                ov.ReadFile(conn.fileno(), nbytes)
        except BrokenPipeError:
            return self._result(b'')

        def finish_recv(trans, key, ov):
            try:
                return ov.getresult()
            except OSError as exc:
                if exc.winerror == _overlapped.ERROR_NETNAME_DELETED:
                    raise ConnectionResetError(*exc.args)
                else:
                    raise
        return self._register(ov, conn, finish_recv)

    def send(self, conn, buf, flags=0):
        self._register_with_iocp(conn)
        ov = _overlapped.Overlapped(NULL)
        if isinstance(conn, socket.socket):
            ov.WSASend(conn.fileno(), buf, flags)
        else:
            ov.WriteFile(conn.fileno(), buf)

        def finish_send(trans, key, ov):
            try:
                return ov.getresult()
            except OSError as exc:
                if exc.winerror == _overlapped.ERROR_NETNAME_DELETED:
                    raise ConnectionResetError(*exc.args)
                else:
                    raise
        return self._register(ov, conn, finish_send)

    def accept(self, listener):
        self._register_with_iocp(listener)
        conn = self._get_accept_socket(listener.family)
        ov = _overlapped.Overlapped(NULL)
        ov.AcceptEx(listener.fileno(), conn.fileno())

        def finish_accept(trans, key, ov):
            ov.getresult()
            buf = struct.pack('@P', listener.fileno())
            conn.setsockopt(socket.SOL_SOCKET, _overlapped.
                SO_UPDATE_ACCEPT_CONTEXT, buf)
            conn.settimeout(listener.gettimeout())
            return conn, conn.getpeername()

        @coroutine
        def accept_coro(future, conn):
            try:
                yield from future
            except futures.CancelledError:
                conn.close()
                raise
        future = self._register(ov, listener, finish_accept)
        coro = accept_coro(future, conn)
        tasks.ensure_future(coro, loop=self._loop)
        return future

    def connect(self, conn, address):
        self._register_with_iocp(conn)
        try:
            _overlapped.BindLocal(conn.fileno(), conn.family)
        except OSError as e:
            if e.winerror != errno.WSAEINVAL:
                raise
            if conn.getsockname()[1] == 0:
                raise
        ov = _overlapped.Overlapped(NULL)
        ov.ConnectEx(conn.fileno(), address)

        def finish_connect(trans, key, ov):
            ov.getresult()
            conn.setsockopt(socket.SOL_SOCKET, _overlapped.
                SO_UPDATE_CONNECT_CONTEXT, 0)
            return conn
        return self._register(ov, conn, finish_connect)

    def accept_pipe(self, pipe):
        self._register_with_iocp(pipe)
        ov = _overlapped.Overlapped(NULL)
        connected = ov.ConnectNamedPipe(pipe.fileno())
        if connected:
            return self._result(pipe)

        def finish_accept_pipe(trans, key, ov):
            ov.getresult()
            return pipe
        return self._register(ov, pipe, finish_accept_pipe)

    @coroutine
    def connect_pipe(self, address):
        delay = CONNECT_PIPE_INIT_DELAY
        while True:
            try:
                handle = _overlapped.ConnectPipe(address)
                break
            except OSError as exc:
                if exc.winerror != _overlapped.ERROR_PIPE_BUSY:
                    raise
            delay = min(delay * 2, CONNECT_PIPE_MAX_DELAY)
            yield from tasks.sleep(delay, loop=self._loop)
        return windows_utils.PipeHandle(handle)

    def wait_for_handle(self, handle, timeout=None):
        """Wait for a handle.

        Return a Future object. The result of the future is True if the wait
        completed, or False if the wait did not complete (on timeout).
        """
        return self._wait_for_handle(handle, timeout, False)

    def _wait_cancel(self, event, done_callback):
        fut = self._wait_for_handle(event, None, True)
        fut._done_callback = done_callback
        return fut

    def _wait_for_handle(self, handle, timeout, _is_cancel):
        if timeout is None:
            ms = _winapi.INFINITE
        else:
            ms = math.ceil(timeout * 1000.0)
        ov = _overlapped.Overlapped(NULL)
        wait_handle = _overlapped.RegisterWaitWithQueue(handle, self._iocp,
            ov.address, ms)
        if _is_cancel:
            f = _WaitCancelFuture(ov, handle, wait_handle, loop=self._loop)
        else:
            f = _WaitHandleFuture(ov, handle, wait_handle, self, loop=self.
                _loop)
        if f._source_traceback:
            del f._source_traceback[-1]

        def finish_wait_for_handle(trans, key, ov):
            return f._poll()
        self._cache[ov.address] = f, ov, 0, finish_wait_for_handle
        return f

    def _register_with_iocp(self, obj):
        if obj not in self._registered:
            self._registered.add(obj)
            _overlapped.CreateIoCompletionPort(obj.fileno(), self._iocp, 0, 0)

    def _register(self, ov, obj, callback):
        f = _OverlappedFuture(ov, loop=self._loop)
        if f._source_traceback:
            del f._source_traceback[-1]
        if not ov.pending:
            try:
                value = callback(None, None, ov)
            except OSError as e:
                f.set_exception(e)
            else:
                f.set_result(value)
        self._cache[ov.address] = f, ov, obj, callback
        return f

    def _unregister(self, ov):
        """Unregister an overlapped object.

        Call this method when its future has been cancelled. The event can
        already be signalled (pending in the proactor event queue). It is also
        safe if the event is never signalled (because it was cancelled).
        """
        self._unregistered.append(ov)

    def _get_accept_socket(self, family):
        s = socket.socket(family)
        s.settimeout(0)
        return s

    def _poll(self, timeout=None):
        if timeout is None:
            ms = INFINITE
        elif timeout < 0:
            raise ValueError('negative timeout')
        else:
            ms = math.ceil(timeout * 1000.0)
            if ms >= INFINITE:
                raise ValueError('timeout too big')
        while True:
            status = _overlapped.GetQueuedCompletionStatus(self._iocp, ms)
            if status is None:
                break
            ms = 0
            err, transferred, key, address = status
            try:
                f, ov, obj, callback = self._cache.pop(address)
            except KeyError:
                if self._loop.get_debug():
                    self._loop.call_exception_handler({'message':
                        'GetQueuedCompletionStatus() returned an unexpected event'
                        , 'status': 
                        'err=%s transferred=%s key=%#x address=%#x' % (err,
                        transferred, key, address)})
                if key not in (0, _overlapped.INVALID_HANDLE_VALUE):
                    _winapi.CloseHandle(key)
                continue
            if obj in self._stopped_serving:
                f.cancel()
            elif not f.done():
                try:
                    value = callback(transferred, key, ov)
                except OSError as e:
                    f.set_exception(e)
                    self._results.append(f)
                else:
                    f.set_result(value)
                    self._results.append(f)
        for ov in self._unregistered:
            self._cache.pop(ov.address, None)
        self._unregistered.clear()

    def _stop_serving(self, obj):
        self._stopped_serving.add(obj)

    def close(self):
        for address, (fut, ov, obj, callback) in list(self._cache.items()):
            if fut.cancelled():
                pass
            elif isinstance(fut, _WaitCancelFuture):
                pass
            else:
                try:
                    fut.cancel()
                except OSError as exc:
                    if self._loop is not None:
                        context = {'message': 'Cancelling a future failed',
                            'exception': exc, 'future': fut}
                        if fut._source_traceback:
                            context['source_traceback'] = fut._source_traceback
                        self._loop.call_exception_handler(context)
        while self._cache:
            if not self._poll(1):
                logger.debug('taking long time to close proactor')
        self._results = []
        if self._iocp is not None:
            _winapi.CloseHandle(self._iocp)
            self._iocp = None

    def __del__(self):
        self.close()


class _WindowsSubprocessTransport(base_subprocess.BaseSubprocessTransport):

    def _start(self, args, shell, stdin, stdout, stderr, bufsize, **kwargs):
        self._proc = windows_utils.Popen(args, shell=shell, stdin=stdin,
            stdout=stdout, stderr=stderr, bufsize=bufsize, **kwargs)

        def callback(f):
            returncode = self._proc.poll()
            self._process_exited(returncode)
        f = self._loop._proactor.wait_for_handle(int(self._proc._handle))
        f.add_done_callback(callback)


SelectorEventLoop = _WindowsSelectorEventLoop


class _WindowsDefaultEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
    _loop_factory = SelectorEventLoop


DefaultEventLoopPolicy = _WindowsDefaultEventLoopPolicy
