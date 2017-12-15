import sys
from . import context
globals().update((name, getattr(context._default_context, name)) for name in
    context._default_context.__all__)
__all__ = context._default_context.__all__
SUBDEBUG = 5
SUBWARNING = 25
if '__main__' in sys.modules:
    sys.modules['__mp_main__'] = sys.modules['__main__']
