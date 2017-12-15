"""
A number of functions that enhance IDLE on Mac OSX.
"""
from sys import platform
import tkinter
_tk_type = None


def _init_tk_type():
    """
    Initializes OS X Tk variant values for
    isAquaTk(), isCarbonTk(), isCocoaTk(), and isXQuartz().
    """
    global _tk_type
    if platform == 'darwin':
        root = tkinter.Tk()
        ws = root.tk.call('tk', 'windowingsystem')
        if 'x11' in ws:
            _tk_type = 'xquartz'
        elif 'aqua' not in ws:
            _tk_type = 'other'
        elif 'AppKit' in root.tk.call('winfo', 'server', '.'):
            _tk_type = 'cocoa'
        else:
            _tk_type = 'carbon'
        root.destroy()
    else:
        _tk_type = 'other'


def isAquaTk():
    """
    Returns True if IDLE is using a native OS X Tk (Cocoa or Carbon).
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == 'cocoa' or _tk_type == 'carbon'


def isCarbonTk():
    """
    Returns True if IDLE is using a Carbon Aqua Tk (instead of the
    newer Cocoa Aqua Tk).
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == 'carbon'


def isCocoaTk():
    """
    Returns True if IDLE is using a Cocoa Aqua Tk.
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == 'cocoa'


def isXQuartz():
    """
    Returns True if IDLE is using an OS X X11 Tk.
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == 'xquartz'


def tkVersionWarning(root):
    """
    Returns a string warning message if the Tk version in use appears to
    be one known to cause problems with IDLE.
    1. Apple Cocoa-based Tk 8.5.7 shipped with Mac OS X 10.6 is unusable.
    2. Apple Cocoa-based Tk 8.5.9 in OS X 10.7 and 10.8 is better but
        can still crash unexpectedly.
    """
    if isCocoaTk():
        patchlevel = root.tk.call('info', 'patchlevel')
        if patchlevel not in ('8.5.7', '8.5.9'):
            return False
        return (
            'WARNING: The version of Tcl/Tk ({0}) in use may be unstable.\\nVisit http://www.python.org/download/mac/tcltk/ for current information.'
            .format(patchlevel))
    else:
        return False


def addOpenEventSupport(root, flist):
    """
    This ensures that the application will respond to open AppleEvents, which
    makes is feasible to use IDLE as the default application for python files.
    """

    def doOpenFile(*args):
        for fn in args:
            flist.open(fn)
    root.createcommand('::tk::mac::OpenDocument', doOpenFile)


def hideTkConsole(root):
    try:
        root.tk.call('console', 'hide')
    except tkinter.TclError:
        pass


def overrideRootMenu(root, flist):
    """
    Replace the Tk root menu by something that is more appropriate for
    IDLE with an Aqua Tk.
    """
    from tkinter import Menu
    from idlelib import mainmenu
    from idlelib import windows
    closeItem = mainmenu.menudefs[0][1][-2]
    del mainmenu.menudefs[0][1][-3:]
    mainmenu.menudefs[0][1].insert(6, closeItem)
    del mainmenu.menudefs[-1][1][0:2]
    del mainmenu.menudefs[-2][1][0]
    menubar = Menu(root)
    root.configure(menu=menubar)
    menudict = {}
    menudict['windows'] = menu = Menu(menubar, name='windows', tearoff=0)
    menubar.add_cascade(label='Window', menu=menu, underline=0)

    def postwindowsmenu(menu=menu):
        end = menu.index('end')
        if end is None:
            end = -1
        if end > 0:
            menu.delete(0, end)
        windows.add_windows_to_menu(menu)
    windows.register_callback(postwindowsmenu)

    def about_dialog(event=None):
        """Handle Help 'About IDLE' event."""
        from idlelib import help_about
        help_about.AboutDialog(root, 'About IDLE')

    def config_dialog(event=None):
        """Handle Options 'Configure IDLE' event."""
        from idlelib import configdialog
        root.instance_dict = flist.inversedict
        configdialog.ConfigDialog(root, 'Settings')

    def help_dialog(event=None):
        """Handle Help 'IDLE Help' event."""
        from idlelib import help
        help.show_idlehelp(root)
    root.bind('<<about-idle>>', about_dialog)
    root.bind('<<open-config-dialog>>', config_dialog)
    root.createcommand('::tk::mac::ShowPreferences', config_dialog)
    if flist:
        root.bind('<<close-all-windows>>', flist.close_all_callback)
        root.createcommand('exit', flist.close_all_callback)
    if isCarbonTk():
        menudict['application'] = menu = Menu(menubar, name='apple', tearoff=0)
        menubar.add_cascade(label='IDLE', menu=menu)
        mainmenu.menudefs.insert(0, ('application', [('About IDLE',
            '<<about-idle>>'), None]))
    if isCocoaTk():
        root.createcommand('tkAboutDialog', about_dialog)
        root.createcommand('::tk::mac::ShowHelp', help_dialog)
        del mainmenu.menudefs[-1][1][0]


def fixb2context(root):
    """Removed bad AquaTk Button-2 (right) and Paste bindings.

    They prevent context menu access and seem to be gone in AquaTk8.6.
    See issue #24801.
    """
    root.unbind_class('Text', '<B2>')
    root.unbind_class('Text', '<B2-Motion>')
    root.unbind_class('Text', '<<PasteSelection>>')


def setupApp(root, flist):
    """
    Perform initial OS X customizations if needed.
    Called from pyshell.main() after initial calls to Tk()

    There are currently three major versions of Tk in use on OS X:
        1. Aqua Cocoa Tk (native default since OS X 10.6)
        2. Aqua Carbon Tk (original native, 32-bit only, deprecated)
        3. X11 (supported by some third-party distributors, deprecated)
    There are various differences among the three that affect IDLE
    behavior, primarily with menus, mouse key events, and accelerators.
    Some one-time customizations are performed here.
    Others are dynamically tested throughout idlelib by calls to the
    isAquaTk(), isCarbonTk(), isCocoaTk(), isXQuartz() functions which
    are initialized here as well.
    """
    if isAquaTk():
        hideTkConsole(root)
        overrideRootMenu(root, flist)
        addOpenEventSupport(root, flist)
        fixb2context(root)


if __name__ == '__main__':
    from unittest import main
    main('idlelib.idle_test.test_macosx', verbosity=2)
