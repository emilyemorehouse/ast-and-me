import array
import unittest
from test.support import import_module, get_attribute
import os, struct
fcntl = import_module('fcntl')
termios = import_module('termios')
get_attribute(termios, 'TIOCGPGRP')
try:
    tty = open('/dev/tty', 'rb')
except OSError:
    raise unittest.SkipTest('Unable to open /dev/tty')
else:
    r = fcntl.ioctl(tty, termios.TIOCGPGRP, '    ')
    tty.close()
    rpgrp = struct.unpack('i', r)[0]
    if rpgrp not in (os.getpgrp(), os.getsid(0)):
        raise unittest.SkipTest(
            'Neither the process group nor the session are attached to /dev/tty'
            )
    del tty, r, rpgrp
try:
    import pty
except ImportError:
    pty = None


class IoctlTests(unittest.TestCase):

    def test_ioctl(self):
        ids = os.getpgrp(), os.getsid(0)
        with open('/dev/tty', 'rb') as tty:
            r = fcntl.ioctl(tty, termios.TIOCGPGRP, '    ')
            rpgrp = struct.unpack('i', r)[0]
            self.assertIn(rpgrp, ids)

    def _check_ioctl_mutate_len(self, nbytes=None):
        buf = array.array('i')
        intsize = buf.itemsize
        ids = os.getpgrp(), os.getsid(0)
        fill = -12345
        if nbytes is not None:
            buf.extend([fill] * (nbytes // intsize))
            self.assertEqual(len(buf) * intsize, nbytes)
        else:
            buf.append(fill)
        with open('/dev/tty', 'rb') as tty:
            r = fcntl.ioctl(tty, termios.TIOCGPGRP, buf, 1)
        rpgrp = buf[0]
        self.assertEqual(r, 0)
        self.assertIn(rpgrp, ids)

    def test_ioctl_mutate(self):
        self._check_ioctl_mutate_len()

    def test_ioctl_mutate_1024(self):
        self._check_ioctl_mutate_len(1024)

    def test_ioctl_mutate_2048(self):
        self._check_ioctl_mutate_len(2048)

    def test_ioctl_signed_unsigned_code_param(self):
        if not pty:
            raise unittest.SkipTest('pty module required')
        mfd, sfd = pty.openpty()
        try:
            if termios.TIOCSWINSZ < 0:
                set_winsz_opcode_maybe_neg = termios.TIOCSWINSZ
                set_winsz_opcode_pos = termios.TIOCSWINSZ & 4294967295
            else:
                set_winsz_opcode_pos = termios.TIOCSWINSZ
                set_winsz_opcode_maybe_neg, = struct.unpack('i', struct.
                    pack('I', termios.TIOCSWINSZ))
            our_winsz = struct.pack('HHHH', 80, 25, 0, 0)
            new_winsz = fcntl.ioctl(mfd, set_winsz_opcode_pos, our_winsz)
            new_winsz = fcntl.ioctl(mfd, set_winsz_opcode_maybe_neg, our_winsz)
        finally:
            os.close(mfd)
            os.close(sfd)


if __name__ == '__main__':
    unittest.main()
