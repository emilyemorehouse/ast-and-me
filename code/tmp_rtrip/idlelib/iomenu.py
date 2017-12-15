import codecs
from codecs import BOM_UTF8
import os
import re
import shlex
import sys
import tempfile
import tkinter.filedialog as tkFileDialog
import tkinter.messagebox as tkMessageBox
from tkinter.simpledialog import askstring
import idlelib
from idlelib.config import idleConf
if idlelib.testing:
    encoding = 'utf-8'
else:
    try:
        import locale
        locale.setlocale(locale.LC_CTYPE, '')
    except (ImportError, locale.Error):
        pass
    locale_decode = 'ascii'
    if sys.platform == 'win32':
        try:
            locale_encoding = locale.getdefaultlocale()[1]
            codecs.lookup(locale_encoding)
        except LookupError:
            pass
    else:
        try:
            locale_encoding = locale.nl_langinfo(locale.CODESET)
            if locale_encoding is None or locale_encoding is '':
                locale_encoding = 'ascii'
            codecs.lookup(locale_encoding)
        except (NameError, AttributeError, LookupError):
            try:
                locale_encoding = locale.getdefaultlocale()[1]
                if locale_encoding is None or locale_encoding is '':
                    locale_encoding = 'ascii'
                codecs.lookup(locale_encoding)
            except (ValueError, LookupError):
                pass
    locale_encoding = locale_encoding.lower()
    encoding = locale_encoding
coding_re = re.compile('^[ \\t\\f]*#.*?coding[:=][ \\t]*([-\\w.]+)', re.ASCII)
blank_re = re.compile('^[ \\t\\f]*(?:[#\\r\\n]|$)', re.ASCII)


def coding_spec(data):
    """Return the encoding declaration according to PEP 263.

    When checking encoded data, only the first two lines should be passed
    in to avoid a UnicodeDecodeError if the rest of the data is not unicode.
    The first two lines would contain the encoding specification.

    Raise a LookupError if the encoding is declared but unknown.
    """
    if isinstance(data, bytes):
        lines = data.decode('iso-8859-1')
    else:
        lines = data
    if '\n' in lines:
        lst = lines.split('\n', 2)[:2]
    elif '\r' in lines:
        lst = lines.split('\r', 2)[:2]
    else:
        lst = [lines]
    for line in lst:
        match = coding_re.match(line)
        if match is not None:
            break
        if not blank_re.match(line):
            return None
    else:
        return None
    name = match.group(1)
    try:
        codecs.lookup(name)
    except LookupError:
        raise LookupError('Unknown encoding: ' + name)
    return name


class IOBinding:

    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text
        self.__id_open = self.text.bind('<<open-window-from-file>>', self.open)
        self.__id_save = self.text.bind('<<save-window>>', self.save)
        self.__id_saveas = self.text.bind('<<save-window-as-file>>', self.
            save_as)
        self.__id_savecopy = self.text.bind('<<save-copy-of-window-as-file>>',
            self.save_a_copy)
        self.fileencoding = None
        self.__id_print = self.text.bind('<<print-window>>', self.print_window)

    def close(self):
        self.text.unbind('<<open-window-from-file>>', self.__id_open)
        self.text.unbind('<<save-window>>', self.__id_save)
        self.text.unbind('<<save-window-as-file>>', self.__id_saveas)
        self.text.unbind('<<save-copy-of-window-as-file>>', self.__id_savecopy)
        self.text.unbind('<<print-window>>', self.__id_print)
        self.editwin = None
        self.text = None
        self.filename_change_hook = None

    def get_saved(self):
        return self.editwin.get_saved()

    def set_saved(self, flag):
        self.editwin.set_saved(flag)

    def reset_undo(self):
        self.editwin.reset_undo()
    filename_change_hook = None

    def set_filename_change_hook(self, hook):
        self.filename_change_hook = hook
    filename = None
    dirname = None

    def set_filename(self, filename):
        if filename and os.path.isdir(filename):
            self.filename = None
            self.dirname = filename
        else:
            self.filename = filename
            self.dirname = None
            self.set_saved(1)
            if self.filename_change_hook:
                self.filename_change_hook()

    def open(self, event=None, editFile=None):
        flist = self.editwin.flist
        if flist:
            if not editFile:
                filename = self.askopenfile()
            else:
                filename = editFile
            if filename:
                if self.editwin and not getattr(self.editwin, 'interp', None
                    ) and not self.filename and self.get_saved():
                    flist.open(filename, self.loadfile)
                else:
                    flist.open(filename)
            elif self.text:
                self.text.focus_set()
            return 'break'
        if self.get_saved():
            reply = self.maybesave()
            if reply == 'cancel':
                self.text.focus_set()
                return 'break'
        if not editFile:
            filename = self.askopenfile()
        else:
            filename = editFile
        if filename:
            self.loadfile(filename)
        else:
            self.text.focus_set()
        return 'break'
    eol = '(\\r\\n)|\\n|\\r'
    eol_re = re.compile(eol)
    eol_convention = os.linesep

    def loadfile(self, filename):
        try:
            with open(filename, 'rb') as f:
                two_lines = f.readline() + f.readline()
                f.seek(0)
                bytes = f.read()
        except OSError as msg:
            tkMessageBox.showerror('I/O Error', str(msg), parent=self.text)
            return False
        chars, converted = self._decode(two_lines, bytes)
        if chars is None:
            tkMessageBox.showerror('Decoding Error', 
                'File %s\nFailed to Decode' % filename, parent=self.text)
            return False
        firsteol = self.eol_re.search(chars)
        if firsteol:
            self.eol_convention = firsteol.group(0)
            chars = self.eol_re.sub('\\n', chars)
        self.text.delete('1.0', 'end')
        self.set_filename(None)
        self.text.insert('1.0', chars)
        self.reset_undo()
        self.set_filename(filename)
        if converted:
            self.set_saved(False)
        self.text.mark_set('insert', '1.0')
        self.text.yview('insert')
        self.updaterecentfileslist(filename)
        return True

    def _decode(self, two_lines, bytes):
        """Create a Unicode string."""
        chars = None
        if bytes.startswith(BOM_UTF8):
            try:
                chars = bytes[3:].decode('utf-8')
            except UnicodeDecodeError:
                return None, False
            else:
                self.fileencoding = 'BOM'
                return chars, False
        try:
            enc = coding_spec(two_lines)
        except LookupError as name:
            tkMessageBox.showerror(title='Error loading the file', message=
                "The encoding '%s' is not known to this Python installation. The file may not display correctly"
                 % name, parent=self.text)
            enc = None
        except UnicodeDecodeError:
            return None, False
        if enc:
            try:
                chars = str(bytes, enc)
                self.fileencoding = enc
                return chars, False
            except UnicodeDecodeError:
                pass
        try:
            chars = str(bytes, 'ascii')
            self.fileencoding = None
            return chars, False
        except UnicodeDecodeError:
            pass
        try:
            chars = str(bytes, 'utf-8')
            self.fileencoding = 'utf-8'
            return chars, False
        except UnicodeDecodeError:
            pass
        try:
            self.editwin.text.update()
            enc = askstring('Specify file encoding',
                """The file's encoding is invalid for Python 3.x.
IDLE will convert it to UTF-8.
What is the current encoding of the file?"""
                , initialvalue=encoding, parent=self.editwin.text)
            if enc:
                chars = str(bytes, enc)
                self.fileencoding = None
            return chars, True
        except (UnicodeDecodeError, LookupError):
            pass
        return None, False

    def maybesave(self):
        if self.get_saved():
            return 'yes'
        message = 'Do you want to save %s before closing?' % (self.filename or
            'this untitled document')
        confirm = tkMessageBox.askyesnocancel(title='Save On Close',
            message=message, default=tkMessageBox.YES, parent=self.text)
        if confirm:
            reply = 'yes'
            self.save(None)
            if not self.get_saved():
                reply = 'cancel'
        elif confirm is None:
            reply = 'cancel'
        else:
            reply = 'no'
        self.text.focus_set()
        return reply

    def save(self, event):
        if not self.filename:
            self.save_as(event)
        elif self.writefile(self.filename):
            self.set_saved(True)
            try:
                self.editwin.store_file_breaks()
            except AttributeError:
                pass
        self.text.focus_set()
        return 'break'

    def save_as(self, event):
        filename = self.asksavefile()
        if filename:
            if self.writefile(filename):
                self.set_filename(filename)
                self.set_saved(1)
                try:
                    self.editwin.store_file_breaks()
                except AttributeError:
                    pass
        self.text.focus_set()
        self.updaterecentfileslist(filename)
        return 'break'

    def save_a_copy(self, event):
        filename = self.asksavefile()
        if filename:
            self.writefile(filename)
        self.text.focus_set()
        self.updaterecentfileslist(filename)
        return 'break'

    def writefile(self, filename):
        self.fixlastline()
        text = self.text.get('1.0', 'end-1c')
        if self.eol_convention != '\n':
            text = text.replace('\n', self.eol_convention)
        chars = self.encode(text)
        try:
            with open(filename, 'wb') as f:
                f.write(chars)
            return True
        except OSError as msg:
            tkMessageBox.showerror('I/O Error', str(msg), parent=self.text)
            return False

    def encode(self, chars):
        if isinstance(chars, bytes):
            return chars
        if self.fileencoding == 'BOM':
            return BOM_UTF8 + chars.encode('utf-8')
        try:
            return chars.encode('ascii')
        except UnicodeError:
            pass
        try:
            enc = coding_spec(chars)
            failed = None
        except LookupError as msg:
            failed = msg
            enc = None
        else:
            if not enc:
                enc = 'utf-8'
        if enc:
            try:
                return chars.encode(enc)
            except UnicodeError:
                failed = "Invalid encoding '%s'" % enc
        tkMessageBox.showerror('I/O Error', '%s.\nSaving as UTF-8' % failed,
            parent=self.text)
        return BOM_UTF8 + chars.encode('utf-8')

    def fixlastline(self):
        c = self.text.get('end-2c')
        if c != '\n':
            self.text.insert('end-1c', '\n')

    def print_window(self, event):
        confirm = tkMessageBox.askokcancel(title='Print', message=
            'Print to Default Printer', default=tkMessageBox.OK, parent=
            self.text)
        if not confirm:
            self.text.focus_set()
            return 'break'
        tempfilename = None
        saved = self.get_saved()
        if saved:
            filename = self.filename
        if not saved or filename is None:
            tfd, tempfilename = tempfile.mkstemp(prefix='IDLE_tmp_')
            filename = tempfilename
            os.close(tfd)
            if not self.writefile(tempfilename):
                os.unlink(tempfilename)
                return 'break'
        platform = os.name
        printPlatform = True
        if platform == 'posix':
            command = idleConf.GetOption('main', 'General',
                'print-command-posix')
            command = command + ' 2>&1'
        elif platform == 'nt':
            command = idleConf.GetOption('main', 'General', 'print-command-win'
                )
        else:
            printPlatform = False
        if printPlatform:
            command = command % shlex.quote(filename)
            pipe = os.popen(command, 'r')
            output = pipe.read().strip()
            status = pipe.close()
            if status:
                output = ('Printing failed (exit status 0x%x)\n' % status +
                    output)
            if output:
                output = 'Printing command: %s\n' % repr(command) + output
                tkMessageBox.showerror('Print status', output, parent=self.text
                    )
        else:
            message = ('Printing is not enabled for this platform: %s' %
                platform)
            tkMessageBox.showinfo('Print status', message, parent=self.text)
        if tempfilename:
            os.unlink(tempfilename)
        return 'break'
    opendialog = None
    savedialog = None
    filetypes = [('Python files', '*.py *.pyw', 'TEXT'), ('Text files',
        '*.txt', 'TEXT'), ('All files', '*')]
    defaultextension = '.py' if sys.platform == 'darwin' else ''

    def askopenfile(self):
        dir, base = self.defaultfilename('open')
        if not self.opendialog:
            self.opendialog = tkFileDialog.Open(parent=self.text, filetypes
                =self.filetypes)
        filename = self.opendialog.show(initialdir=dir, initialfile=base)
        return filename

    def defaultfilename(self, mode='open'):
        if self.filename:
            return os.path.split(self.filename)
        elif self.dirname:
            return self.dirname, ''
        else:
            try:
                pwd = os.getcwd()
            except OSError:
                pwd = ''
            return pwd, ''

    def asksavefile(self):
        dir, base = self.defaultfilename('save')
        if not self.savedialog:
            self.savedialog = tkFileDialog.SaveAs(parent=self.text,
                filetypes=self.filetypes, defaultextension=self.
                defaultextension)
        filename = self.savedialog.show(initialdir=dir, initialfile=base)
        return filename

    def updaterecentfileslist(self, filename):
        """Update recent file list on all editor windows"""
        if self.editwin.flist:
            self.editwin.update_recent_files_list(filename)


def _io_binding(parent):
    from tkinter import Toplevel, Text
    root = Toplevel(parent)
    root.title('Test IOBinding')
    x, y = map(int, parent.geometry().split('+')[1:])
    root.geometry('+%d+%d' % (x, y + 175))


    class MyEditWin:

        def __init__(self, text):
            self.text = text
            self.flist = None
            self.text.bind('<Control-o>', self.open)
            self.text.bind('<Control-p>', self.print)
            self.text.bind('<Control-s>', self.save)
            self.text.bind('<Alt-s>', self.saveas)
            self.text.bind('<Control-c>', self.savecopy)

        def get_saved(self):
            return 0

        def set_saved(self, flag):
            pass

        def reset_undo(self):
            pass

        def open(self, event):
            self.text.event_generate('<<open-window-from-file>>')

        def print(self, event):
            self.text.event_generate('<<print-window>>')

        def save(self, event):
            self.text.event_generate('<<save-window>>')

        def saveas(self, event):
            self.text.event_generate('<<save-window-as-file>>')

        def savecopy(self, event):
            self.text.event_generate('<<save-copy-of-window-as-file>>')
    text = Text(root)
    text.pack()
    text.focus_set()
    editwin = MyEditWin(text)
    IOBinding(editwin)


if __name__ == '__main__':
    import unittest
    unittest.main('idlelib.idle_test.test_iomenu', verbosity=2, exit=False)
    from idlelib.idle_test.htest import run
    run(_io_binding)
