import os
import sys
import runpy
import types
from . import get_start_method, set_start_method
from . import process
from .context import reduction
from . import util
__all__ = ['_main', 'freeze_support', 'set_executable', 'get_executable',
    'get_preparation_data', 'get_command_line', 'import_main_path']
if sys.platform != 'win32':
    WINEXE = False
    WINSERVICE = False
else:
    WINEXE = sys.platform == 'win32' and getattr(sys, 'frozen', False)
    WINSERVICE = sys.executable.lower().endswith('pythonservice.exe')
if WINSERVICE:
    _python_exe = os.path.join(sys.exec_prefix, 'python.exe')
else:
    _python_exe = sys.executable


def set_executable(exe):
    global _python_exe
    _python_exe = exe


def get_executable():
    return _python_exe


def is_forking(argv):
    """
    Return whether commandline indicates we are forking
    """
    if len(argv) >= 2 and argv[1] == '--multiprocessing-fork':
        return True
    else:
        return False


def freeze_support():
    """
    Run code for process object if this in not the main process
    """
    if is_forking(sys.argv):
        kwds = {}
        for arg in sys.argv[2:]:
            name, value = arg.split('=')
            if value == 'None':
                kwds[name] = None
            else:
                kwds[name] = int(value)
        spawn_main(**kwds)
        sys.exit()


def get_command_line(**kwds):
    """
    Returns prefix of command line used for spawning a child process
    """
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--multiprocessing-fork'] + [('%s=%r' %
            item) for item in kwds.items()]
    else:
        prog = 'from multiprocessing.spawn import spawn_main; spawn_main(%s)'
        prog %= ', '.join('%s=%r' % item for item in kwds.items())
        opts = util._args_from_interpreter_flags()
        return [_python_exe] + opts + ['-c', prog, '--multiprocessing-fork']


def spawn_main(pipe_handle, parent_pid=None, tracker_fd=None):
    """
    Run code specified by data received over pipe
    """
    assert is_forking(sys.argv)
    if sys.platform == 'win32':
        import msvcrt
        new_handle = reduction.steal_handle(parent_pid, pipe_handle)
        fd = msvcrt.open_osfhandle(new_handle, os.O_RDONLY)
    else:
        from . import semaphore_tracker
        semaphore_tracker._semaphore_tracker._fd = tracker_fd
        fd = pipe_handle
    exitcode = _main(fd)
    sys.exit(exitcode)


def _main(fd):
    with os.fdopen(fd, 'rb', closefd=True) as from_parent:
        process.current_process()._inheriting = True
        try:
            preparation_data = reduction.pickle.load(from_parent)
            prepare(preparation_data)
            self = reduction.pickle.load(from_parent)
        finally:
            del process.current_process()._inheriting
    return self._bootstrap()


def _check_not_importing_main():
    if getattr(process.current_process(), '_inheriting', False):
        raise RuntimeError(
            """
        An attempt has been made to start a new process before the
        current process has finished its bootstrapping phase.

        This probably means that you are not using fork to start your
        child processes and you have forgotten to use the proper idiom
        in the main module:

            if __name__ == '__main__':
                freeze_support()
                ...

        The "freeze_support()" line can be omitted if the program
        is not going to be frozen to produce an executable."""
            )


def get_preparation_data(name):
    """
    Return info about parent needed by child to unpickle process object
    """
    _check_not_importing_main()
    d = dict(log_to_stderr=util._log_to_stderr, authkey=process.
        current_process().authkey)
    if util._logger is not None:
        d['log_level'] = util._logger.getEffectiveLevel()
    sys_path = sys.path.copy()
    try:
        i = sys_path.index('')
    except ValueError:
        pass
    else:
        sys_path[i] = process.ORIGINAL_DIR
    d.update(name=name, sys_path=sys_path, sys_argv=sys.argv, orig_dir=
        process.ORIGINAL_DIR, dir=os.getcwd(), start_method=get_start_method())
    main_module = sys.modules['__main__']
    main_mod_name = getattr(main_module.__spec__, 'name', None)
    if main_mod_name is not None:
        d['init_main_from_name'] = main_mod_name
    elif sys.platform != 'win32' or not WINEXE and not WINSERVICE:
        main_path = getattr(main_module, '__file__', None)
        if main_path is not None:
            if not os.path.isabs(main_path
                ) and process.ORIGINAL_DIR is not None:
                main_path = os.path.join(process.ORIGINAL_DIR, main_path)
            d['init_main_from_path'] = os.path.normpath(main_path)
    return d


old_main_modules = []


def prepare(data):
    """
    Try to get current process ready to unpickle process object
    """
    if 'name' in data:
        process.current_process().name = data['name']
    if 'authkey' in data:
        process.current_process().authkey = data['authkey']
    if 'log_to_stderr' in data and data['log_to_stderr']:
        util.log_to_stderr()
    if 'log_level' in data:
        util.get_logger().setLevel(data['log_level'])
    if 'sys_path' in data:
        sys.path = data['sys_path']
    if 'sys_argv' in data:
        sys.argv = data['sys_argv']
    if 'dir' in data:
        os.chdir(data['dir'])
    if 'orig_dir' in data:
        process.ORIGINAL_DIR = data['orig_dir']
    if 'start_method' in data:
        set_start_method(data['start_method'], force=True)
    if 'init_main_from_name' in data:
        _fixup_main_from_name(data['init_main_from_name'])
    elif 'init_main_from_path' in data:
        _fixup_main_from_path(data['init_main_from_path'])


def _fixup_main_from_name(mod_name):
    current_main = sys.modules['__main__']
    if mod_name == '__main__' or mod_name.endswith('.__main__'):
        return
    if getattr(current_main.__spec__, 'name', None) == mod_name:
        return
    old_main_modules.append(current_main)
    main_module = types.ModuleType('__mp_main__')
    main_content = runpy.run_module(mod_name, run_name='__mp_main__',
        alter_sys=True)
    main_module.__dict__.update(main_content)
    sys.modules['__main__'] = sys.modules['__mp_main__'] = main_module


def _fixup_main_from_path(main_path):
    current_main = sys.modules['__main__']
    main_name = os.path.splitext(os.path.basename(main_path))[0]
    if main_name == 'ipython':
        return
    if getattr(current_main, '__file__', None) == main_path:
        return
    old_main_modules.append(current_main)
    main_module = types.ModuleType('__mp_main__')
    main_content = runpy.run_path(main_path, run_name='__mp_main__')
    main_module.__dict__.update(main_content)
    sys.modules['__main__'] = sys.modules['__mp_main__'] = main_module


def import_main_path(main_path):
    """
    Set sys.modules['__main__'] to module at main_path
    """
    _fixup_main_from_path(main_path)
