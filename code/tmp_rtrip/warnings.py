"""Python part of the warnings subsystem."""
import sys
__all__ = ['warn', 'warn_explicit', 'showwarning', 'formatwarning',
    'filterwarnings', 'simplefilter', 'resetwarnings', 'catch_warnings']


def showwarning(message, category, filename, lineno, file=None, line=None):
    """Hook to write a warning to a file; replace if you like."""
    msg = WarningMessage(message, category, filename, lineno, file, line)
    _showwarnmsg_impl(msg)


def formatwarning(message, category, filename, lineno, line=None):
    """Function to format a warning the standard way."""
    msg = WarningMessage(message, category, filename, lineno, None, line)
    return _formatwarnmsg_impl(msg)


def _showwarnmsg_impl(msg):
    file = msg.file
    if file is None:
        file = sys.stderr
        if file is None:
            return
    text = _formatwarnmsg(msg)
    try:
        file.write(text)
    except OSError:
        pass


def _formatwarnmsg_impl(msg):
    s = '%s:%s: %s: %s\n' % (msg.filename, msg.lineno, msg.category.
        __name__, msg.message)
    if msg.line is None:
        try:
            import linecache
            line = linecache.getline(msg.filename, msg.lineno)
        except Exception:
            line = None
            linecache = None
    else:
        line = msg.line
    if line:
        line = line.strip()
        s += '  %s\n' % line
    if msg.source is not None:
        try:
            import tracemalloc
            tb = tracemalloc.get_object_traceback(msg.source)
        except Exception:
            tb = None
        if tb is not None:
            s += 'Object allocated at (most recent call first):\n'
            for frame in tb:
                s += '  File "%s", lineno %s\n' % (frame.filename, frame.lineno
                    )
                try:
                    if linecache is not None:
                        line = linecache.getline(frame.filename, frame.lineno)
                    else:
                        line = None
                except Exception:
                    line = None
                if line:
                    line = line.strip()
                    s += '    %s\n' % line
    return s


_showwarning_orig = showwarning


def _showwarnmsg(msg):
    """Hook to write a warning to a file; replace if you like."""
    try:
        sw = showwarning
    except NameError:
        pass
    else:
        if sw is not _showwarning_orig:
            if not callable(sw):
                raise TypeError(
                    'warnings.showwarning() must be set to a function or method'
                    )
            sw(msg.message, msg.category, msg.filename, msg.lineno, msg.
                file, msg.line)
            return
    _showwarnmsg_impl(msg)


_formatwarning_orig = formatwarning


def _formatwarnmsg(msg):
    """Function to format a warning the standard way."""
    try:
        fw = formatwarning
    except NameError:
        pass
    else:
        if fw is not _formatwarning_orig:
            return fw(msg.message, msg.category, msg.filename, msg.lineno,
                line=msg.line)
    return _formatwarnmsg_impl(msg)


def filterwarnings(action, message='', category=Warning, module='', lineno=
    0, append=False):
    """Insert an entry into the list of warnings filters (at the front).

    'action' -- one of "error", "ignore", "always", "default", "module",
                or "once"
    'message' -- a regex that the warning message must match
    'category' -- a class that the warning must be a subclass of
    'module' -- a regex that the module name must match
    'lineno' -- an integer line number, 0 matches all warnings
    'append' -- if true, append to the list of filters
    """
    import re
    assert action in ('error', 'ignore', 'always', 'default', 'module', 'once'
        ), 'invalid action: %r' % (action,)
    assert isinstance(message, str), 'message must be a string'
    assert isinstance(category, type), 'category must be a class'
    assert issubclass(category, Warning), 'category must be a Warning subclass'
    assert isinstance(module, str), 'module must be a string'
    assert isinstance(lineno, int
        ) and lineno >= 0, 'lineno must be an int >= 0'
    _add_filter(action, re.compile(message, re.I), category, re.compile(
        module), lineno, append=append)


def simplefilter(action, category=Warning, lineno=0, append=False):
    """Insert a simple entry into the list of warnings filters (at the front).

    A simple filter matches all modules and messages.
    'action' -- one of "error", "ignore", "always", "default", "module",
                or "once"
    'category' -- a class that the warning must be a subclass of
    'lineno' -- an integer line number, 0 matches all warnings
    'append' -- if true, append to the list of filters
    """
    assert action in ('error', 'ignore', 'always', 'default', 'module', 'once'
        ), 'invalid action: %r' % (action,)
    assert isinstance(lineno, int
        ) and lineno >= 0, 'lineno must be an int >= 0'
    _add_filter(action, None, category, None, lineno, append=append)


def _add_filter(*item, append):
    if not append:
        try:
            filters.remove(item)
        except ValueError:
            pass
        filters.insert(0, item)
    elif item not in filters:
        filters.append(item)
    _filters_mutated()


def resetwarnings():
    """Clear the list of warning filters, so that no filters are active."""
    filters[:] = []
    _filters_mutated()


class _OptionError(Exception):
    """Exception used by option processing helpers."""
    pass


def _processoptions(args):
    for arg in args:
        try:
            _setoption(arg)
        except _OptionError as msg:
            print('Invalid -W option ignored:', msg, file=sys.stderr)


def _setoption(arg):
    import re
    parts = arg.split(':')
    if len(parts) > 5:
        raise _OptionError('too many fields (max 5): %r' % (arg,))
    while len(parts) < 5:
        parts.append('')
    action, message, category, module, lineno = [s.strip() for s in parts]
    action = _getaction(action)
    message = re.escape(message)
    category = _getcategory(category)
    module = re.escape(module)
    if module:
        module = module + '$'
    if lineno:
        try:
            lineno = int(lineno)
            if lineno < 0:
                raise ValueError
        except (ValueError, OverflowError):
            raise _OptionError('invalid lineno %r' % (lineno,))
    else:
        lineno = 0
    filterwarnings(action, message, category, module, lineno)


def _getaction(action):
    if not action:
        return 'default'
    if action == 'all':
        return 'always'
    for a in ('default', 'always', 'ignore', 'module', 'once', 'error'):
        if a.startswith(action):
            return a
    raise _OptionError('invalid action: %r' % (action,))


def _getcategory(category):
    import re
    if not category:
        return Warning
    if re.match('^[a-zA-Z0-9_]+$', category):
        try:
            cat = eval(category)
        except NameError:
            raise _OptionError('unknown warning category: %r' % (category,))
    else:
        i = category.rfind('.')
        module = category[:i]
        klass = category[i + 1:]
        try:
            m = __import__(module, None, None, [klass])
        except ImportError:
            raise _OptionError('invalid module name: %r' % (module,))
        try:
            cat = getattr(m, klass)
        except AttributeError:
            raise _OptionError('unknown warning category: %r' % (category,))
    if not issubclass(cat, Warning):
        raise _OptionError('invalid warning category: %r' % (category,))
    return cat


def _is_internal_frame(frame):
    """Signal whether the frame is an internal CPython implementation detail."""
    filename = frame.f_code.co_filename
    return 'importlib' in filename and '_bootstrap' in filename


def _next_external_frame(frame):
    """Find the next frame that doesn't involve CPython internals."""
    frame = frame.f_back
    while frame is not None and _is_internal_frame(frame):
        frame = frame.f_back
    return frame


def warn(message, category=None, stacklevel=1, source=None):
    """Issue a warning, or maybe ignore it or raise an exception."""
    if isinstance(message, Warning):
        category = message.__class__
    if category is None:
        category = UserWarning
    if not (isinstance(category, type) and issubclass(category, Warning)):
        raise TypeError("category must be a Warning subclass, not '{:s}'".
            format(type(category).__name__))
    try:
        if stacklevel <= 1 or _is_internal_frame(sys._getframe(1)):
            frame = sys._getframe(stacklevel)
        else:
            frame = sys._getframe(1)
            for x in range(stacklevel - 1):
                frame = _next_external_frame(frame)
                if frame is None:
                    raise ValueError
    except ValueError:
        globals = sys.__dict__
        lineno = 1
    else:
        globals = frame.f_globals
        lineno = frame.f_lineno
    if '__name__' in globals:
        module = globals['__name__']
    else:
        module = '<string>'
    filename = globals.get('__file__')
    if filename:
        fnl = filename.lower()
        if fnl.endswith('.pyc'):
            filename = filename[:-1]
    else:
        if module == '__main__':
            try:
                filename = sys.argv[0]
            except AttributeError:
                filename = '__main__'
        if not filename:
            filename = module
    registry = globals.setdefault('__warningregistry__', {})
    warn_explicit(message, category, filename, lineno, module, registry,
        globals, source)


def warn_explicit(message, category, filename, lineno, module=None,
    registry=None, module_globals=None, source=None):
    lineno = int(lineno)
    if module is None:
        module = filename or '<unknown>'
        if module[-3:].lower() == '.py':
            module = module[:-3]
    if registry is None:
        registry = {}
    if registry.get('version', 0) != _filters_version:
        registry.clear()
        registry['version'] = _filters_version
    if isinstance(message, Warning):
        text = str(message)
        category = message.__class__
    else:
        text = message
        message = category(message)
    key = text, category, lineno
    if registry.get(key):
        return
    for item in filters:
        action, msg, cat, mod, ln = item
        if (msg is None or msg.match(text)) and issubclass(category, cat) and (
            mod is None or mod.match(module)) and (ln == 0 or lineno == ln):
            break
    else:
        action = defaultaction
    if action == 'ignore':
        registry[key] = 1
        return
    import linecache
    linecache.getlines(filename, module_globals)
    if action == 'error':
        raise message
    if action == 'once':
        registry[key] = 1
        oncekey = text, category
        if onceregistry.get(oncekey):
            return
        onceregistry[oncekey] = 1
    elif action == 'always':
        pass
    elif action == 'module':
        registry[key] = 1
        altkey = text, category, 0
        if registry.get(altkey):
            return
        registry[altkey] = 1
    elif action == 'default':
        registry[key] = 1
    else:
        raise RuntimeError(
            'Unrecognized action (%r) in warnings.filters:\n %s' % (action,
            item))
    msg = WarningMessage(message, category, filename, lineno, source)
    _showwarnmsg(msg)


class WarningMessage(object):
    _WARNING_DETAILS = ('message', 'category', 'filename', 'lineno', 'file',
        'line', 'source')

    def __init__(self, message, category, filename, lineno, file=None, line
        =None, source=None):
        local_values = locals()
        for attr in self._WARNING_DETAILS:
            setattr(self, attr, local_values[attr])
        self._category_name = category.__name__ if category else None

    def __str__(self):
        return (
            '{message : %r, category : %r, filename : %r, lineno : %s, line : %r}'
             % (self.message, self._category_name, self.filename, self.
            lineno, self.line))


class catch_warnings(object):
    """A context manager that copies and restores the warnings filter upon
    exiting the context.

    The 'record' argument specifies whether warnings should be captured by a
    custom implementation of warnings.showwarning() and be appended to a list
    returned by the context manager. Otherwise None is returned by the context
    manager. The objects appended to the list are arguments whose attributes
    mirror the arguments to showwarning().

    The 'module' argument is to specify an alternative module to the module
    named 'warnings' and imported under that name. This argument is only useful
    when testing the warnings module itself.

    """

    def __init__(self, *, record=False, module=None):
        """Specify whether to record warnings and if an alternative module
        should be used other than sys.modules['warnings'].

        For compatibility with Python 3.0, please consider all arguments to be
        keyword-only.

        """
        self._record = record
        self._module = sys.modules['warnings'] if module is None else module
        self._entered = False

    def __repr__(self):
        args = []
        if self._record:
            args.append('record=True')
        if self._module is not sys.modules['warnings']:
            args.append('module=%r' % self._module)
        name = type(self).__name__
        return '%s(%s)' % (name, ', '.join(args))

    def __enter__(self):
        if self._entered:
            raise RuntimeError('Cannot enter %r twice' % self)
        self._entered = True
        self._filters = self._module.filters
        self._module.filters = self._filters[:]
        self._module._filters_mutated()
        self._showwarning = self._module.showwarning
        self._showwarnmsg_impl = self._module._showwarnmsg_impl
        if self._record:
            log = []
            self._module._showwarnmsg_impl = log.append
            self._module.showwarning = self._module._showwarning_orig
            return log
        else:
            return None

    def __exit__(self, *exc_info):
        if not self._entered:
            raise RuntimeError('Cannot exit %r without entering first' % self)
        self._module.filters = self._filters
        self._module._filters_mutated()
        self._module.showwarning = self._showwarning
        self._module._showwarnmsg_impl = self._showwarnmsg_impl


_warnings_defaults = False
try:
    from _warnings import filters, _defaultaction, _onceregistry, warn, warn_explicit, _filters_mutated
    defaultaction = _defaultaction
    onceregistry = _onceregistry
    _warnings_defaults = True
except ImportError:
    filters = []
    defaultaction = 'default'
    onceregistry = {}
    _filters_version = 1

    def _filters_mutated():
        global _filters_version
        _filters_version += 1
_processoptions(sys.warnoptions)
if not _warnings_defaults:
    silence = [ImportWarning, PendingDeprecationWarning]
    silence.append(DeprecationWarning)
    for cls in silence:
        simplefilter('ignore', category=cls)
    bytes_warning = sys.flags.bytes_warning
    if bytes_warning > 1:
        bytes_action = 'error'
    elif bytes_warning:
        bytes_action = 'default'
    else:
        bytes_action = 'ignore'
    simplefilter(bytes_action, category=BytesWarning, append=1)
    if hasattr(sys, 'gettotalrefcount'):
        resource_action = 'always'
    else:
        resource_action = 'ignore'
    simplefilter(resource_action, category=ResourceWarning, append=1)
del _warnings_defaults
