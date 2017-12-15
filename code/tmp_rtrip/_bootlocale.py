"""A minimal subset of the locale module used at interpreter startup
(imported by the _io module), in order to reduce startup time.

Don't import directly from third-party code; use the `locale` module instead!
"""
import sys
import _locale
if sys.platform.startswith('win'):

    def getpreferredencoding(do_setlocale=True):
        return _locale._getdefaultlocale()[1]
else:
    try:
        _locale.CODESET
    except AttributeError:

        def getpreferredencoding(do_setlocale=True):
            import locale
            return locale.getpreferredencoding(do_setlocale)
    else:

        def getpreferredencoding(do_setlocale=True):
            assert not do_setlocale
            result = _locale.nl_langinfo(_locale.CODESET)
            if not result and sys.platform == 'darwin':
                result = 'UTF-8'
            return result
