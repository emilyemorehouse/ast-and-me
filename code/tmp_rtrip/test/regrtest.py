"""
Script to run Python regression tests.

Run this script with -h or --help for documentation.
"""
import importlib
import os
import sys
from test.libregrtest import main
main_in_temp_cwd = main


def _main():
    global __file__
    mydir = os.path.abspath(os.path.normpath(os.path.dirname(sys.argv[0])))
    i = len(sys.path) - 1
    while i >= 0:
        if os.path.abspath(os.path.normpath(sys.path[i])) == mydir:
            del sys.path[i]
        else:
            i -= 1
    __file__ = os.path.abspath(__file__)
    assert __file__ == os.path.abspath(sys.argv[0])
    main()


if __name__ == '__main__':
    _main()
