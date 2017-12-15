"""The asyncio package, tracking PEP 3156."""
import sys
try:
    from . import selectors
except ImportError:
    import selectors
if sys.platform == 'win32':
    try:
        from . import _overlapped
    except ImportError:
        import _overlapped
from .base_events import *
from .coroutines import *
from .events import *
from .futures import *
from .locks import *
from .protocols import *
from .queues import *
from .streams import *
from .subprocess import *
from .tasks import *
from .transports import *
__all__ = (base_events.__all__ + coroutines.__all__ + events.__all__ +
    futures.__all__ + locks.__all__ + protocols.__all__ + queues.__all__ +
    streams.__all__ + subprocess.__all__ + tasks.__all__ + transports.__all__)
if sys.platform == 'win32':
    from .windows_events import *
    __all__ += windows_events.__all__
else:
    from .unix_events import *
    __all__ += unix_events.__all__
