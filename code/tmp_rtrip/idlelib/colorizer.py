import builtins
import keyword
import re
import time
from idlelib.config import idleConf
from idlelib.delegator import Delegator
DEBUG = False


def any(name, alternates):
    """Return a named group pattern matching list of alternates."""
    return '(?P<%s>' % name + '|'.join(alternates) + ')'


def make_pat():
    kw = '\\b' + any('KEYWORD', keyword.kwlist) + '\\b'
    builtinlist = [str(name) for name in dir(builtins) if not name.
        startswith('_') and name not in keyword.kwlist]
    builtin = '([^.\'\\"\\\\#]\\b|^)' + any('BUILTIN', builtinlist) + '\\b'
    comment = any('COMMENT', ['#[^\\n]*'])
    stringprefix = '(?i:\\br|u|f|fr|rf|b|br|rb)?'
    sqstring = stringprefix + "'[^'\\\\\\n]*(\\\\.[^'\\\\\\n]*)*'?"
    dqstring = stringprefix + '"[^"\\\\\\n]*(\\\\.[^"\\\\\\n]*)*"?'
    sq3string = stringprefix + "'''[^'\\\\]*((\\\\.|'(?!''))[^'\\\\]*)*(''')?"
    dq3string = stringprefix + '"""[^"\\\\]*((\\\\.|"(?!""))[^"\\\\]*)*(""")?'
    string = any('STRING', [sq3string, dq3string, sqstring, dqstring])
    return kw + '|' + builtin + '|' + comment + '|' + string + '|' + any('SYNC'
        , ['\\n'])


prog = re.compile(make_pat(), re.S)
idprog = re.compile('\\s+(\\w+)', re.S)


def color_config(text):
    """Set color opitons of Text widget.

    Should be called whenever ColorDelegator is called.
    """
    theme = idleConf.CurrentTheme()
    normal_colors = idleConf.GetHighlight(theme, 'normal')
    cursor_color = idleConf.GetHighlight(theme, 'cursor', fgBg='fg')
    select_colors = idleConf.GetHighlight(theme, 'hilite')
    text.config(foreground=normal_colors['foreground'], background=
        normal_colors['background'], insertbackground=cursor_color,
        selectforeground=select_colors['foreground'], selectbackground=
        select_colors['background'], inactiveselectbackground=select_colors
        ['background'])


class ColorDelegator(Delegator):

    def __init__(self):
        Delegator.__init__(self)
        self.prog = prog
        self.idprog = idprog
        self.LoadTagDefs()

    def setdelegate(self, delegate):
        if self.delegate is not None:
            self.unbind('<<toggle-auto-coloring>>')
        Delegator.setdelegate(self, delegate)
        if delegate is not None:
            self.config_colors()
            self.bind('<<toggle-auto-coloring>>', self.toggle_colorize_event)
            self.notify_range('1.0', 'end')
        else:
            self.stop_colorizing = True
            self.allow_colorizing = False

    def config_colors(self):
        for tag, cnf in self.tagdefs.items():
            if cnf:
                self.tag_configure(tag, **cnf)
        self.tag_raise('sel')

    def LoadTagDefs(self):
        theme = idleConf.CurrentTheme()
        self.tagdefs = {'COMMENT': idleConf.GetHighlight(theme, 'comment'),
            'KEYWORD': idleConf.GetHighlight(theme, 'keyword'), 'BUILTIN':
            idleConf.GetHighlight(theme, 'builtin'), 'STRING': idleConf.
            GetHighlight(theme, 'string'), 'DEFINITION': idleConf.
            GetHighlight(theme, 'definition'), 'SYNC': {'background': None,
            'foreground': None}, 'TODO': {'background': None, 'foreground':
            None}, 'ERROR': idleConf.GetHighlight(theme, 'error'), 'hit':
            idleConf.GetHighlight(theme, 'hit')}
        if DEBUG:
            print('tagdefs', self.tagdefs)

    def insert(self, index, chars, tags=None):
        index = self.index(index)
        self.delegate.insert(index, chars, tags)
        self.notify_range(index, index + '+%dc' % len(chars))

    def delete(self, index1, index2=None):
        index1 = self.index(index1)
        self.delegate.delete(index1, index2)
        self.notify_range(index1)
    after_id = None
    allow_colorizing = True
    colorizing = False

    def notify_range(self, index1, index2=None):
        self.tag_add('TODO', index1, index2)
        if self.after_id:
            if DEBUG:
                print('colorizing already scheduled')
            return
        if self.colorizing:
            self.stop_colorizing = True
            if DEBUG:
                print('stop colorizing')
        if self.allow_colorizing:
            if DEBUG:
                print('schedule colorizing')
            self.after_id = self.after(1, self.recolorize)
    close_when_done = None

    def close(self, close_when_done=None):
        if self.after_id:
            after_id = self.after_id
            self.after_id = None
            if DEBUG:
                print('cancel scheduled recolorizer')
            self.after_cancel(after_id)
        self.allow_colorizing = False
        self.stop_colorizing = True
        if close_when_done:
            if not self.colorizing:
                close_when_done.destroy()
            else:
                self.close_when_done = close_when_done

    def toggle_colorize_event(self, event):
        if self.after_id:
            after_id = self.after_id
            self.after_id = None
            if DEBUG:
                print('cancel scheduled recolorizer')
            self.after_cancel(after_id)
        if self.allow_colorizing and self.colorizing:
            if DEBUG:
                print('stop colorizing')
            self.stop_colorizing = True
        self.allow_colorizing = not self.allow_colorizing
        if self.allow_colorizing and not self.colorizing:
            self.after_id = self.after(1, self.recolorize)
        if DEBUG:
            print('auto colorizing turned', self.allow_colorizing and 'on' or
                'off')
        return 'break'

    def recolorize(self):
        self.after_id = None
        if not self.delegate:
            if DEBUG:
                print('no delegate')
            return
        if not self.allow_colorizing:
            if DEBUG:
                print('auto colorizing is off')
            return
        if self.colorizing:
            if DEBUG:
                print('already colorizing')
            return
        try:
            self.stop_colorizing = False
            self.colorizing = True
            if DEBUG:
                print('colorizing...')
            t0 = time.perf_counter()
            self.recolorize_main()
            t1 = time.perf_counter()
            if DEBUG:
                print('%.3f seconds' % (t1 - t0))
        finally:
            self.colorizing = False
        if self.allow_colorizing and self.tag_nextrange('TODO', '1.0'):
            if DEBUG:
                print('reschedule colorizing')
            self.after_id = self.after(1, self.recolorize)
        if self.close_when_done:
            top = self.close_when_done
            self.close_when_done = None
            top.destroy()

    def recolorize_main(self):
        next = '1.0'
        while True:
            item = self.tag_nextrange('TODO', next)
            if not item:
                break
            head, tail = item
            self.tag_remove('SYNC', head, tail)
            item = self.tag_prevrange('SYNC', head)
            if item:
                head = item[1]
            else:
                head = '1.0'
            chars = ''
            next = head
            lines_to_get = 1
            ok = False
            while not ok:
                mark = next
                next = self.index(mark + '+%d lines linestart' % lines_to_get)
                lines_to_get = min(lines_to_get * 2, 100)
                ok = 'SYNC' in self.tag_names(next + '-1c')
                line = self.get(mark, next)
                if not line:
                    return
                for tag in self.tagdefs:
                    self.tag_remove(tag, mark, next)
                chars = chars + line
                m = self.prog.search(chars)
                while m:
                    for key, value in m.groupdict().items():
                        if value:
                            a, b = m.span(key)
                            self.tag_add(key, head + '+%dc' % a, head + 
                                '+%dc' % b)
                            if value in ('def', 'class'):
                                m1 = self.idprog.match(chars, b)
                                if m1:
                                    a, b = m1.span(1)
                                    self.tag_add('DEFINITION', head + 
                                        '+%dc' % a, head + '+%dc' % b)
                    m = self.prog.search(chars, m.end())
                if 'SYNC' in self.tag_names(next + '-1c'):
                    head = next
                    chars = ''
                else:
                    ok = False
                if not ok:
                    self.tag_add('TODO', next)
                self.update()
                if self.stop_colorizing:
                    if DEBUG:
                        print('colorizing stopped')
                    return

    def removecolors(self):
        for tag in self.tagdefs:
            self.tag_remove(tag, '1.0', 'end')


def _color_delegator(parent):
    from tkinter import Toplevel, Text
    from idlelib.percolator import Percolator
    top = Toplevel(parent)
    top.title('Test ColorDelegator')
    x, y = map(int, parent.geometry().split('+')[1:])
    top.geometry('700x250+%d+%d' % (x + 20, y + 175))
    source = """# Following has syntax errors
if True: then int 1
elif False: print 0
else: float(None)
if iF + If + IF: 'keywork matching must respect case'
# All valid prefixes for unicode and byte strings should be colored
'x', '''x''', "x", ""\"x""\"
r'x', u'x', R'x', U'x', f'x', F'x', ur'is invalid'
fr'x', Fr'x', fR'x', FR'x', rf'x', rF'x', Rf'x', RF'x'
b'x',B'x', br'x',Br'x',bR'x',BR'x', rb'x'.rB'x',Rb'x',RB'x'
"""
    text = Text(top, background='white')
    text.pack(expand=1, fill='both')
    text.insert('insert', source)
    text.focus_set()
    color_config(text)
    p = Percolator(text)
    d = ColorDelegator()
    p.insertfilter(d)


if __name__ == '__main__':
    import unittest
    unittest.main('idlelib.idle_test.test_colorizer', verbosity=2, exit=False)
    from idlelib.idle_test.htest import run
    run(_color_delegator)
