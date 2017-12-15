"""Main entry point"""
import sys
if sys.argv[0].endswith('__main__.py'):
    import os.path
    executable = os.path.basename(sys.executable)
    sys.argv[0] = executable + ' -m unittest'
    del os
__unittest = True
from .main import main, TestProgram
main(module=None)
