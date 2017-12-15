import os
import shutil
import subprocess
import sys
if os.name == 'nt':

    def _get_build_version():
        """Return the version of MSVC that was used to build Python.

        For Python 2.3 and up, the version number is included in
        sys.version.  For earlier versions, assume the compiler is MSVC 6.
        """
        prefix = 'MSC v.'
        i = sys.version.find(prefix)
        if i == -1:
            return 6
        i = i + len(prefix)
        s, rest = sys.version[i:].split(' ', 1)
        majorVersion = int(s[:-2]) - 6
        if majorVersion >= 13:
            majorVersion += 1
        minorVersion = int(s[2:3]) / 10.0
        if majorVersion == 6:
            minorVersion = 0
        if majorVersion >= 6:
            return majorVersion + minorVersion
        return None

    def find_msvcrt():
        """Return the name of the VC runtime dll"""
        version = _get_build_version()
        if version is None:
            return None
        if version <= 6:
            clibname = 'msvcrt'
        elif version <= 13:
            clibname = 'msvcr%d' % (version * 10)
        else:
            return None
        import importlib.machinery
        if '_d.pyd' in importlib.machinery.EXTENSION_SUFFIXES:
            clibname += 'd'
        return clibname + '.dll'

    def find_library(name):
        if name in ('c', 'm'):
            return find_msvcrt()
        for directory in os.environ['PATH'].split(os.pathsep):
            fname = os.path.join(directory, name)
            if os.path.isfile(fname):
                return fname
            if fname.lower().endswith('.dll'):
                continue
            fname = fname + '.dll'
            if os.path.isfile(fname):
                return fname
        return None
if os.name == 'posix' and sys.platform == 'darwin':
    from ctypes.macholib.dyld import dyld_find as _dyld_find

    def find_library(name):
        possible = ['lib%s.dylib' % name, '%s.dylib' % name, 
            '%s.framework/%s' % (name, name)]
        for name in possible:
            try:
                return _dyld_find(name)
            except ValueError:
                continue
        return None
elif os.name == 'posix':
    import re, tempfile

    def _findLib_gcc(name):
        expr = os.fsencode('[^\\(\\)\\s]*lib%s\\.[^\\(\\)\\s]*' % re.escape
            (name))
        c_compiler = shutil.which('gcc')
        if not c_compiler:
            c_compiler = shutil.which('cc')
        if not c_compiler:
            return None
        temp = tempfile.NamedTemporaryFile()
        try:
            args = [c_compiler, '-Wl,-t', '-o', temp.name, '-l' + name]
            env = dict(os.environ)
            env['LC_ALL'] = 'C'
            env['LANG'] = 'C'
            try:
                proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, env=env)
            except OSError:
                return None
            with proc:
                trace = proc.stdout.read()
        finally:
            try:
                temp.close()
            except FileNotFoundError:
                pass
        res = re.search(expr, trace)
        if not res:
            return None
        return os.fsdecode(res.group(0))
    if sys.platform == 'sunos5':

        def _get_soname(f):
            if not f:
                return None
            try:
                proc = subprocess.Popen(('/usr/ccs/bin/dump', '-Lpv', f),
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            except OSError:
                return None
            with proc:
                data = proc.stdout.read()
            res = re.search(b'\\[.*\\]\\sSONAME\\s+([^\\s]+)', data)
            if not res:
                return None
            return os.fsdecode(res.group(1))
    else:

        def _get_soname(f):
            if not f:
                return None
            objdump = shutil.which('objdump')
            if not objdump:
                return None
            try:
                proc = subprocess.Popen((objdump, '-p', '-j', '.dynamic', f
                    ), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            except OSError:
                return None
            with proc:
                dump = proc.stdout.read()
            res = re.search(b'\\sSONAME\\s+([^\\s]+)', dump)
            if not res:
                return None
            return os.fsdecode(res.group(1))
    if sys.platform.startswith(('freebsd', 'openbsd', 'dragonfly')):

        def _num_version(libname):
            parts = libname.split(b'.')
            nums = []
            try:
                while parts:
                    nums.insert(0, int(parts.pop()))
            except ValueError:
                pass
            return nums or [sys.maxsize]

        def find_library(name):
            ename = re.escape(name)
            expr = ':-l%s\\.\\S+ => \\S*/(lib%s\\.\\S+)' % (ename, ename)
            expr = os.fsencode(expr)
            try:
                proc = subprocess.Popen(('/sbin/ldconfig', '-r'), stdout=
                    subprocess.PIPE, stderr=subprocess.DEVNULL)
            except OSError:
                data = b''
            else:
                with proc:
                    data = proc.stdout.read()
            res = re.findall(expr, data)
            if not res:
                return _get_soname(_findLib_gcc(name))
            res.sort(key=_num_version)
            return os.fsdecode(res[-1])
    elif sys.platform == 'sunos5':

        def _findLib_crle(name, is64):
            if not os.path.exists('/usr/bin/crle'):
                return None
            env = dict(os.environ)
            env['LC_ALL'] = 'C'
            if is64:
                args = '/usr/bin/crle', '-64'
            else:
                args = '/usr/bin/crle',
            paths = None
            try:
                proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, env=env)
            except OSError:
                return None
            with proc:
                for line in proc.stdout:
                    line = line.strip()
                    if line.startswith(b'Default Library Path (ELF):'):
                        paths = os.fsdecode(line).split()[4]
            if not paths:
                return None
            for dir in paths.split(':'):
                libfile = os.path.join(dir, 'lib%s.so' % name)
                if os.path.exists(libfile):
                    return libfile
            return None

        def find_library(name, is64=False):
            return _get_soname(_findLib_crle(name, is64) or _findLib_gcc(name))
    else:

        def _findSoname_ldconfig(name):
            import struct
            if struct.calcsize('l') == 4:
                machine = os.uname().machine + '-32'
            else:
                machine = os.uname().machine + '-64'
            mach_map = {'x86_64-64': 'libc6,x86-64', 'ppc64-64':
                'libc6,64bit', 'sparc64-64': 'libc6,64bit', 's390x-64':
                'libc6,64bit', 'ia64-64': 'libc6,IA-64'}
            abi_type = mach_map.get(machine, 'libc6')
            regex = '\\s+(lib%s\\.[^\\s]+)\\s+\\(%s'
            regex = os.fsencode(regex % (re.escape(name), abi_type))
            try:
                with subprocess.Popen(['/sbin/ldconfig', '-p'], stdin=
                    subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdout=
                    subprocess.PIPE, env={'LC_ALL': 'C', 'LANG': 'C'}) as p:
                    res = re.search(regex, p.stdout.read())
                    if res:
                        return os.fsdecode(res.group(1))
            except OSError:
                pass

        def _findLib_ld(name):
            expr = '[^\\(\\)\\s]*lib%s\\.[^\\(\\)\\s]*' % re.escape(name)
            cmd = ['ld', '-t']
            libpath = os.environ.get('LD_LIBRARY_PATH')
            if libpath:
                for d in libpath.split(':'):
                    cmd.extend(['-L', d])
            cmd.extend(['-o', os.devnull, '-l%s' % name])
            result = None
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=
                    subprocess.PIPE, universal_newlines=True)
                out, _ = p.communicate()
                res = re.search(expr, os.fsdecode(out))
                if res:
                    result = res.group(0)
            except Exception as e:
                pass
            return result

        def find_library(name):
            return _findSoname_ldconfig(name) or _get_soname(_findLib_gcc(
                name) or _findLib_ld(name))


def test():
    from ctypes import cdll
    if os.name == 'nt':
        print(cdll.msvcrt)
        print(cdll.load('msvcrt'))
        print(find_library('msvcrt'))
    if os.name == 'posix':
        print(find_library('m'))
        print(find_library('c'))
        print(find_library('bz2'))
        if sys.platform == 'darwin':
            print(cdll.LoadLibrary('libm.dylib'))
            print(cdll.LoadLibrary('libcrypto.dylib'))
            print(cdll.LoadLibrary('libSystem.dylib'))
            print(cdll.LoadLibrary('System.framework/System'))
        else:
            print(cdll.LoadLibrary('libm.so'))
            print(cdll.LoadLibrary('libcrypt.so'))
            print(find_library('crypt'))


if __name__ == '__main__':
    test()
