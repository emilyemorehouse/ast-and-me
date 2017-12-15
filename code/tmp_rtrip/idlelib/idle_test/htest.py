"""Run human tests of Idle's window, dialog, and popup widgets.

run(*tests)
Create a master Tk window.  Within that, run each callable in tests
after finding the matching test spec in this file.  If tests is empty,
run an htest for each spec dict in this file after finding the matching
callable in the module named in the spec.  Close the window to skip or
end the test.

In a tested module, let X be a global name bound to a callable (class
or function) whose .__name__ attrubute is also X (the usual situation).
The first parameter of X must be 'parent'.  When called, the parent
argument will be the root window.  X must create a child Toplevel
window (or subclass thereof).  The Toplevel may be a test widget or
dialog, in which case the callable is the corresonding class.  Or the
Toplevel may contain the widget to be tested or set up a context in
which a test widget is invoked.  In this latter case, the callable is a
wrapper function that sets up the Toplevel and other objects.  Wrapper
function names, such as _editor_window', should start with '_'.


End the module with

if __name__ == '__main__':
    <unittest, if there is one>
    from idlelib.idle_test.htest import run
    run(X)

To have wrapper functions and test invocation code ignored by coveragepy
reports, put '# htest #' on the def statement header line.

def _wrapper(parent):  # htest #

Also make sure that the 'if __name__' line matches the above.  Then have
make sure that .coveragerc includes the following.

[report]
exclude_lines =
    .*# htest #
    if __name__ == .__main__.:

(The "." instead of "'" is intentional and necessary.)


To run any X, this file must contain a matching instance of the
following template, with X.__name__ prepended to '_spec'.
When all tests are run, the prefix is use to get X.

_spec = {
    'file': '',
    'kwds': {'title': ''},
    'msg': ""
    }

file (no .py): run() imports file.py.
kwds: augmented with {'parent':root} and passed to X as **kwds.
title: an example kwd; some widgets need this, delete if not.
msg: master window hints about testing the widget.


Modules and classes not being tested at the moment:
pyshell.PyShellEditorWindow
debugger.Debugger
autocomplete_w.AutoCompleteWindow
outwin.OutputWindow (indirectly being tested with grep test)
"""
from importlib import import_module
import tkinter as tk
from tkinter.ttk import Scrollbar
tk.NoDefaultRoot()
AboutDialog_spec = {'file': 'help_about', 'kwds': {'title':
    'help_about test', '_htest': True}, 'msg':
    """Test every button. Ensure Python, TK and IDLE versions are correctly displayed.
 [Close] to exit."""
    }
_calltip_window_spec = {'file': 'calltip_w', 'kwds': {}, 'msg':
    """Typing '(' should display a calltip.
Typing ') should hide the calltip.
"""
    }
_class_browser_spec = {'file': 'browser', 'kwds': {}, 'msg':
    """Inspect names of module, class(with superclass if applicable), methods and functions.
Toggle nested items.
Double clicking on items prints a traceback for an exception that is ignored."""
    }
_color_delegator_spec = {'file': 'colorizer', 'kwds': {}, 'msg':
    """The text is sample Python code.
Ensure components like comments, keywords, builtins,
string, definitions, and break are correctly colored.
The default color scheme is in idlelib/config-highlight.def"""
    }
ConfigDialog_spec = {'file': 'configdialog', 'kwds': {'title':
    'ConfigDialogTest', '_htest': True}, 'msg':
    """IDLE preferences dialog.
In the 'Fonts/Tabs' tab, changing font face, should update the font face of the text in the area below it.
In the 'Highlighting' tab, try different color schemes. Clicking items in the sample program should update the choices above it.
In the 'Keys', 'General' and 'Extensions' tabs, test settingsof interest.
[Ok] to close the dialog.[Apply] to apply the settings and and [Cancel] to revert all changes.
Re-run the test to ensure changes made have persisted."""
    }
_dyn_option_menu_spec = {'file': 'dynoption', 'kwds': {}, 'msg':
    """Select one of the many options in the 'old option set'.
Click the button to change the option set.
Select one of the many options in the 'new option set'."""
    }
_editor_window_spec = {'file': 'editor', 'kwds': {}, 'msg':
    """Test editor functions of interest.
Best to close editor first."""}
GetKeysDialog_spec = {'file': 'config_key', 'kwds': {'title':
    'Test keybindings', 'action': 'find-again', 'currentKeySequences': [''],
    '_htest': True}, 'msg':
    """Test for different key modifier sequences.
<nothing> is invalid.
No modifier key is invalid.
Shift key with [a-z],[0-9], function key, move key, tab, spaceis invalid.
No validity checking if advanced key binding entry is used."""
    }
_grep_dialog_spec = {'file': 'grep', 'kwds': {}, 'msg':
    """Click the 'Show GrepDialog' button.
Test the various 'Find-in-files' functions.
The results should be displayed in a new '*Output*' window.
'Right-click'->'Goto file/line' anywhere in the search results should open that file 
in a new EditorWindow."""
    }
HelpSource_spec = {'file': 'query', 'kwds': {'title':
    'Help name and source', 'menuitem': 'test', 'filepath': __file__,
    'used_names': {'abc'}, '_htest': True}, 'msg':
    """Enter menu item name and help file path
'', > than 30 chars, and 'abc' are invalid menu item names.
'' and file does not exist are invalid path items.
Any url ('www...', 'http...') is accepted.
Test Browse with and without path, as cannot unittest.
[Ok] or <Return> prints valid entry to shell
[Cancel] or <Escape> prints None to shell"""
    }
_io_binding_spec = {'file': 'iomenu', 'kwds': {}, 'msg':
    """Test the following bindings.
<Control-o> to open file from dialog.
Edit the file.
<Control-p> to print the file.
<Control-s> to save the file.
<Alt-s> to save-as another file.
<Control-c> to save-copy-as another file.
Check that changes were saved by opening the file elsewhere."""
    }
_multi_call_spec = {'file': 'multicall', 'kwds': {}, 'msg':
    """The following actions should trigger a print to console or IDLE Shell.
Entering and leaving the text area, key entry, <Control-Key>,
<Alt-Key-a>, <Control-Key-a>, <Alt-Control-Key-a>, 
<Control-Button-1>, <Alt-Button-1> and focusing out of the window
are sequences to be tested."""
    }
_multistatus_bar_spec = {'file': 'statusbar', 'kwds': {}, 'msg':
    """Ensure presence of multi-status bar below text area.
Click 'Update Status' to change the multi-status text"""
    }
_object_browser_spec = {'file': 'debugobj', 'kwds': {}, 'msg':
    """Double click on items upto the lowest level.
Attributes of the objects and related information will be displayed side-by-side at each level."""
    }
_path_browser_spec = {'file': 'pathbrowser', 'kwds': {}, 'msg':
    """Test for correct display of all paths in sys.path.
Toggle nested items upto the lowest level.
Double clicking on an item prints a traceback
for an exception that is ignored."""
    }
_percolator_spec = {'file': 'percolator', 'kwds': {}, 'msg':
    """There are two tracers which can be toggled using a checkbox.
Toggling a tracer 'on' by checking it should print traceroutput to the console or to the IDLE shell.
If both the tracers are 'on', the output from the tracer which was switched 'on' later, should be printed first
Test for actions like text entry, and removal."""
    }
Query_spec = {'file': 'query', 'kwds': {'title': 'Query', 'message':
    'Enter something', 'text0': 'Go', '_htest': True}, 'msg':
    """Enter with <Return> or [Ok].  Print valid entry to Shell
Blank line, after stripping, is ignored
Close dialog with valid entry, <Escape>, [Cancel], [X]"""
    }
_replace_dialog_spec = {'file': 'replace', 'kwds': {}, 'msg':
    """Click the 'Replace' button.
Test various replace options in the 'Replace dialog'.
Click [Close] or [X] to close the 'Replace Dialog'."""
    }
_search_dialog_spec = {'file': 'search', 'kwds': {}, 'msg':
    """Click the 'Search' button.
Test various search options in the 'Search dialog'.
Click [Close] or [X] to close the 'Search Dialog'."""
    }
_searchbase_spec = {'file': 'searchbase', 'kwds': {}, 'msg':
    """Check the appearance of the base search dialog
Its only action is to close."""
    }
_scrolled_list_spec = {'file': 'scrolledlist', 'kwds': {}, 'msg':
    """You should see a scrollable list of items
Selecting (clicking) or double clicking an item prints the name to the console or Idle shell.
Right clicking an item will display a popup."""
    }
show_idlehelp_spec = {'file': 'help', 'kwds': {}, 'msg':
    """If the help text displays, this works.
Text is selectable. Window is scrollable."""
    }
_stack_viewer_spec = {'file': 'stackviewer', 'kwds': {}, 'msg':
    """A stacktrace for a NameError exception.
Expand 'idlelib ...' and '<locals>'.
Check that exc_value, exc_tb, and exc_type are correct.
"""
    }
_tabbed_pages_spec = {'file': 'tabbedpages', 'kwds': {}, 'msg':
    """Toggle between the two tabs 'foo' and 'bar'
Add a tab by entering a suitable name for it.
Remove an existing tab by entering its name.
Remove all existing tabs.
<nothing> is an invalid add page and remove page name.
"""
    }
TextViewer_spec = {'file': 'textview', 'kwds': {'title': 'Test textview',
    'text': """The quick brown fox jumps over the lazy dog.
""" * 35,
    '_htest': True}, 'msg':
    """Test for read-only property of text.
Text is selectable. Window is scrollable."""
    }
_tooltip_spec = {'file': 'tooltip', 'kwds': {}, 'msg':
    """Place mouse cursor over both the buttons
A tooltip should appear with some text."""
    }
_tree_widget_spec = {'file': 'tree', 'kwds': {}, 'msg':
    """The canvas is scrollable.
Click on folders upto to the lowest level."""}
_undo_delegator_spec = {'file': 'undo', 'kwds': {}, 'msg':
    """Click [Undo] to undo any action.
Click [Redo] to redo any action.
Click [Dump] to dump the current state by printing to the console or the IDLE shell.
"""
    }
_widget_redirector_spec = {'file': 'redirector', 'kwds': {}, 'msg':
    'Every text insert should be printed to the console.or the IDLE shell.'}


def run(*tests):
    root = tk.Tk()
    root.title('IDLE htest')
    root.resizable(0, 0)
    frameLabel = tk.Frame(root, padx=10)
    frameLabel.pack()
    text = tk.Text(frameLabel, wrap='word')
    text.configure(bg=root.cget('bg'), relief='flat', height=4, width=70)
    scrollbar = Scrollbar(frameLabel, command=text.yview)
    text.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y', expand=False)
    text.pack(side='left', fill='both', expand=True)
    test_list = []
    if tests:
        for test in tests:
            test_spec = globals()[test.__name__ + '_spec']
            test_spec['name'] = test.__name__
            test_list.append((test_spec, test))
    else:
        for k, d in globals().items():
            if k.endswith('_spec'):
                test_name = k[:-5]
                test_spec = d
                test_spec['name'] = test_name
                mod = import_module('idlelib.' + test_spec['file'])
                test = getattr(mod, test_name)
                test_list.append((test_spec, test))
    test_name = tk.StringVar(root)
    callable_object = None
    test_kwds = None

    def next_test():
        nonlocal test_name, callable_object, test_kwds
        if len(test_list) == 1:
            next_button.pack_forget()
        test_spec, callable_object = test_list.pop()
        test_kwds = test_spec['kwds']
        test_kwds['parent'] = root
        test_name.set('Test ' + test_spec['name'])
        text.configure(state='normal')
        text.delete('1.0', 'end')
        text.insert('1.0', test_spec['msg'])
        text.configure(state='disabled')

    def run_test(_=None):
        widget = callable_object(**test_kwds)
        try:
            print(widget.result)
        except AttributeError:
            pass

    def close(_=None):
        root.destroy()
    button = tk.Button(root, textvariable=test_name, default='active',
        command=run_test)
    next_button = tk.Button(root, text='Next', command=next_test)
    button.pack()
    next_button.pack()
    next_button.focus_set()
    root.bind('<Key-Return>', run_test)
    root.bind('<Key-Escape>', close)
    next_test()
    root.mainloop()


if __name__ == '__main__':
    run()
