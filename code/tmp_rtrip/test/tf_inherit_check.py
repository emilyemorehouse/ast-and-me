import sys
import os
from test.support import SuppressCrashReport
with SuppressCrashReport():
    verbose = sys.argv[1] == 'v'
    try:
        fd = int(sys.argv[2])
        try:
            os.write(fd, b'blat')
        except OSError:
            sys.exit(0)
        else:
            if verbose:
                sys.stderr.write('fd %d is open in child' % fd)
            sys.exit(1)
    except Exception:
        if verbose:
            raise
        sys.exit(1)
