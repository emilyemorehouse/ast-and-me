"""
Test suite for OS X interpreter environment variables.
"""
from test.support import EnvironmentVarGuard
import subprocess
import sys
import sysconfig
import unittest


@unittest.skipUnless(sys.platform == 'darwin' and sysconfig.get_config_var(
    'WITH_NEXT_FRAMEWORK'), 'unnecessary on this platform')
class OSXEnvironmentVariableTestCase(unittest.TestCase):

    def _check_sys(self, ev, cond, sv, val=sys.executable + 'dummy'):
        with EnvironmentVarGuard() as evg:
            subpc = [str(sys.executable), '-c', 
                'import sys; sys.exit(2 if "%s" %s %s else 3)' % (val, cond,
                sv)]
            evg.unset(ev)
            rc = subprocess.call(subpc)
            self.assertEqual(rc, 3, 'expected %s not %s %s' % (ev, cond, sv))
            evg.set(ev, val)
            rc = subprocess.call(subpc)
            self.assertEqual(rc, 2, 'expected %s %s %s' % (ev, cond, sv))

    def test_pythonexecutable_sets_sys_executable(self):
        self._check_sys('PYTHONEXECUTABLE', '==', 'sys.executable')


if __name__ == '__main__':
    unittest.main()
