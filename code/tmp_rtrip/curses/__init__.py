"""curses

The main package for curses support for Python.  Normally used by importing
the package, and perhaps a particular module inside it.

   import curses
   from curses import textpad
   curses.initscr()
   ...

"""
from _curses import *
import os as _os
import sys as _sys


def initscr():
    import _curses, curses
    setupterm(term=_os.environ.get('TERM', 'unknown'), fd=_sys.__stdout__.
        fileno())
    stdscr = _curses.initscr()
    for key, value in _curses.__dict__.items():
        if key[0:4] == 'ACS_' or key in ('LINES', 'COLS'):
            setattr(curses, key, value)
    return stdscr


def start_color():
    import _curses, curses
    retval = _curses.start_color()
    if hasattr(_curses, 'COLORS'):
        curses.COLORS = _curses.COLORS
    if hasattr(_curses, 'COLOR_PAIRS'):
        curses.COLOR_PAIRS = _curses.COLOR_PAIRS
    return retval


try:
    has_key
except NameError:
    from .has_key import has_key


def wrapper(func, *args, **kwds):
    """Wrapper function that initializes curses and calls another function,
    restoring normal keyboard/screen behavior on error.
    The callable object 'func' is then passed the main window 'stdscr'
    as its first argument, followed by any other arguments passed to
    wrapper().
    """
    try:
        stdscr = initscr()
        noecho()
        cbreak()
        stdscr.keypad(1)
        try:
            start_color()
        except:
            pass
        return func(stdscr, *args, **kwds)
    finally:
        if 'stdscr' in locals():
            stdscr.keypad(0)
            echo()
            nocbreak()
            endwin()
