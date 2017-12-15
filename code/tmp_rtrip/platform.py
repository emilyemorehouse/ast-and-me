""" This module tries to retrieve as much platform-identifying data as
    possible. It makes this information available via function APIs.

    If called from the command line, it prints the platform
    information concatenated as single string to stdout. The output
    format is useable as part of a filename.

"""
__copyright__ = """
    Copyright (c) 1999-2000, Marc-Andre Lemburg; mailto:mal@lemburg.com
    Copyright (c) 2000-2010, eGenix.com Software GmbH; mailto:info@egenix.com

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee or royalty is hereby granted,
    provided that the above copyright notice appear in all copies and that
    both that copyright notice and this permission notice appear in
    supporting documentation or portions thereof, including modifications,
    that you make.

    EGENIX.COM SOFTWARE GMBH DISCLAIMS ALL WARRANTIES WITH REGARD TO
    THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
    INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
    FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
    NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
    WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

"""
__version__ = '1.0.8'
import collections
import sys, os, re, subprocess
import warnings
try:
    DEV_NULL = os.devnull
except AttributeError:
    if sys.platform in ('dos', 'win32', 'win16'):
        DEV_NULL = 'NUL'
    else:
        DEV_NULL = '/dev/null'
_UNIXCONFDIR = '/etc'
_libc_search = re.compile(
    b'(__libc_init)|(GLIBC_([0-9.]+))|(libc(_\\w+)?\\.so(?:\\.(\\d[0-9.]*))?)',
    re.ASCII)


def libc_ver(executable=sys.executable, lib='', version='', chunksize=16384):
    """ Tries to determine the libc version that the file executable
        (which defaults to the Python interpreter) is linked against.

        Returns a tuple of strings (lib,version) which default to the
        given parameters in case the lookup fails.

        Note that the function has intimate knowledge of how different
        libc versions add symbols to the executable and thus is probably
        only useable for executables compiled using gcc.

        The file is read and scanned in chunks of chunksize bytes.

    """
    if hasattr(os.path, 'realpath'):
        executable = os.path.realpath(executable)
    with open(executable, 'rb') as f:
        binary = f.read(chunksize)
        pos = 0
        while 1:
            if b'libc' in binary or b'GLIBC' in binary:
                m = _libc_search.search(binary, pos)
            else:
                m = None
            if not m:
                binary = f.read(chunksize)
                if not binary:
                    break
                pos = 0
                continue
            libcinit, glibc, glibcversion, so, threads, soversion = [(s.
                decode('latin1') if s is not None else s) for s in m.groups()]
            if libcinit and not lib:
                lib = 'libc'
            elif glibc:
                if lib != 'glibc':
                    lib = 'glibc'
                    version = glibcversion
                elif glibcversion > version:
                    version = glibcversion
            elif so:
                if lib != 'glibc':
                    lib = 'libc'
                    if soversion and soversion > version:
                        version = soversion
                    if threads and version[-len(threads):] != threads:
                        version = version + threads
            pos = m.end()
    return lib, version


def _dist_try_harder(distname, version, id):
    """ Tries some special tricks to get the distribution
        information in case the default method fails.

        Currently supports older SuSE Linux, Caldera OpenLinux and
        Slackware Linux distributions.

    """
    if os.path.exists('/var/adm/inst-log/info'):
        distname = 'SuSE'
        for line in open('/var/adm/inst-log/info'):
            tv = line.split()
            if len(tv) == 2:
                tag, value = tv
            else:
                continue
            if tag == 'MIN_DIST_VERSION':
                version = value.strip()
            elif tag == 'DIST_IDENT':
                values = value.split('-')
                id = values[2]
        return distname, version, id
    if os.path.exists('/etc/.installed'):
        for line in open('/etc/.installed'):
            pkg = line.split('-')
            if len(pkg) >= 2 and pkg[0] == 'OpenLinux':
                return 'OpenLinux', pkg[1], id
    if os.path.isdir('/usr/lib/setup'):
        verfiles = os.listdir('/usr/lib/setup')
        for n in range(len(verfiles) - 1, -1, -1):
            if verfiles[n][:14] != 'slack-version-':
                del verfiles[n]
        if verfiles:
            verfiles.sort()
            distname = 'slackware'
            version = verfiles[-1][14:]
            return distname, version, id
    return distname, version, id


_release_filename = re.compile('(\\w+)[-_](release|version)', re.ASCII)
_lsb_release_version = re.compile('(.+) release ([\\d.]+)[^(]*(?:\\((.+)\\))?',
    re.ASCII)
_release_version = re.compile(
    '([^0-9]+)(?: release )?([\\d.]+)[^(]*(?:\\((.+)\\))?', re.ASCII)
_supported_dists = ('SuSE', 'debian', 'fedora', 'redhat', 'centos',
    'mandrake', 'mandriva', 'rocks', 'slackware', 'yellowdog', 'gentoo',
    'UnitedLinux', 'turbolinux', 'arch', 'mageia')


def _parse_release_file(firstline):
    version = ''
    id = ''
    m = _lsb_release_version.match(firstline)
    if m is not None:
        return tuple(m.groups())
    m = _release_version.match(firstline)
    if m is not None:
        return tuple(m.groups())
    l = firstline.strip().split()
    if l:
        version = l[0]
        if len(l) > 1:
            id = l[1]
    return '', version, id


def linux_distribution(distname='', version='', id='', supported_dists=
    _supported_dists, full_distribution_name=1):
    import warnings
    warnings.warn(
        'dist() and linux_distribution() functions are deprecated in Python 3.5'
        , PendingDeprecationWarning, stacklevel=2)
    return _linux_distribution(distname, version, id, supported_dists,
        full_distribution_name)


def _linux_distribution(distname, version, id, supported_dists,
    full_distribution_name):
    """ Tries to determine the name of the Linux OS distribution name.

        The function first looks for a distribution release file in
        /etc and then reverts to _dist_try_harder() in case no
        suitable files are found.

        supported_dists may be given to define the set of Linux
        distributions to look for. It defaults to a list of currently
        supported Linux distributions identified by their release file
        name.

        If full_distribution_name is true (default), the full
        distribution read from the OS is returned. Otherwise the short
        name taken from supported_dists is used.

        Returns a tuple (distname, version, id) which default to the
        args given as parameters.

    """
    try:
        etc = os.listdir(_UNIXCONFDIR)
    except OSError:
        return distname, version, id
    etc.sort()
    for file in etc:
        m = _release_filename.match(file)
        if m is not None:
            _distname, dummy = m.groups()
            if _distname in supported_dists:
                distname = _distname
                break
    else:
        return _dist_try_harder(distname, version, id)
    with open(os.path.join(_UNIXCONFDIR, file), 'r', encoding='utf-8',
        errors='surrogateescape') as f:
        firstline = f.readline()
    _distname, _version, _id = _parse_release_file(firstline)
    if _distname and full_distribution_name:
        distname = _distname
    if _version:
        version = _version
    if _id:
        id = _id
    return distname, version, id


def dist(distname='', version='', id='', supported_dists=_supported_dists):
    """ Tries to determine the name of the Linux OS distribution name.

        The function first looks for a distribution release file in
        /etc and then reverts to _dist_try_harder() in case no
        suitable files are found.

        Returns a tuple (distname, version, id) which default to the
        args given as parameters.

    """
    import warnings
    warnings.warn(
        'dist() and linux_distribution() functions are deprecated in Python 3.5'
        , PendingDeprecationWarning, stacklevel=2)
    return _linux_distribution(distname, version, id, supported_dists=
        supported_dists, full_distribution_name=0)


def popen(cmd, mode='r', bufsize=-1):
    """ Portable popen() interface.
    """
    import warnings
    warnings.warn('use os.popen instead', DeprecationWarning, stacklevel=2)
    return os.popen(cmd, mode, bufsize)


def _norm_version(version, build=''):
    """ Normalize the version and build strings and return a single
        version string using the format major.minor.build (or patchlevel).
    """
    l = version.split('.')
    if build:
        l.append(build)
    try:
        ints = map(int, l)
    except ValueError:
        strings = l
    else:
        strings = list(map(str, ints))
    version = '.'.join(strings[:3])
    return version


_ver_output = re.compile('(?:([\\w ]+) ([\\w.]+) .*\\[.* ([\\d.]+)\\])')


def _syscmd_ver(system='', release='', version='', supported_platforms=(
    'win32', 'win16', 'dos')):
    """ Tries to figure out the OS version used and returns
        a tuple (system, release, version).

        It uses the "ver" shell command for this which is known
        to exists on Windows, DOS. XXX Others too ?

        In case this fails, the given parameters are used as
        defaults.

    """
    if sys.platform not in supported_platforms:
        return system, release, version
    for cmd in ('ver', 'command /c ver', 'cmd /c ver'):
        try:
            pipe = os.popen(cmd)
            info = pipe.read()
            if pipe.close():
                raise OSError('command failed')
        except OSError as why:
            continue
        else:
            break
    else:
        return system, release, version
    info = info.strip()
    m = _ver_output.match(info)
    if m is not None:
        system, release, version = m.groups()
        if release[-1] == '.':
            release = release[:-1]
        if version[-1] == '.':
            version = version[:-1]
        version = _norm_version(version)
    return system, release, version


_WIN32_CLIENT_RELEASES = {(5, 0): '2000', (5, 1): 'XP', (5, 2):
    '2003Server', (5, None): 'post2003', (6, 0): 'Vista', (6, 1): '7', (6, 
    2): '8', (6, 3): '8.1', (6, None): 'post8.1', (10, 0): '10', (10, None):
    'post10'}
_WIN32_SERVER_RELEASES = {(5, 2): '2003Server', (6, 0): '2008Server', (6, 1
    ): '2008ServerR2', (6, 2): '2012Server', (6, 3): '2012ServerR2', (6,
    None): 'post2012ServerR2'}


def win32_ver(release='', version='', csd='', ptype=''):
    try:
        from sys import getwindowsversion
    except ImportError:
        return release, version, csd, ptype
    try:
        from winreg import OpenKeyEx, QueryValueEx, CloseKey, HKEY_LOCAL_MACHINE
    except ImportError:
        from _winreg import OpenKeyEx, QueryValueEx, CloseKey, HKEY_LOCAL_MACHINE
    winver = getwindowsversion()
    maj, min, build = winver.platform_version or winver[:3]
    version = '{0}.{1}.{2}'.format(maj, min, build)
    release = _WIN32_CLIENT_RELEASES.get((maj, min)
        ) or _WIN32_CLIENT_RELEASES.get((maj, None)) or release
    if winver[:2] == (maj, min):
        try:
            csd = 'SP{}'.format(winver.service_pack_major)
        except AttributeError:
            if csd[:13] == 'Service Pack ':
                csd = 'SP' + csd[13:]
    if getattr(winver, 'product_type', None) == 3:
        release = _WIN32_SERVER_RELEASES.get((maj, min)
            ) or _WIN32_SERVER_RELEASES.get((maj, None)) or release
    key = None
    try:
        key = OpenKeyEx(HKEY_LOCAL_MACHINE,
            'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
        ptype = QueryValueEx(key, 'CurrentType')[0]
    except:
        pass
    finally:
        if key:
            CloseKey(key)
    return release, version, csd, ptype


def _mac_ver_xml():
    fn = '/System/Library/CoreServices/SystemVersion.plist'
    if not os.path.exists(fn):
        return None
    try:
        import plistlib
    except ImportError:
        return None
    with open(fn, 'rb') as f:
        pl = plistlib.load(f)
    release = pl['ProductVersion']
    versioninfo = '', '', ''
    machine = os.uname().machine
    if machine in ('ppc', 'Power Macintosh'):
        machine = 'PowerPC'
    return release, versioninfo, machine


def mac_ver(release='', versioninfo=('', '', ''), machine=''):
    """ Get MacOS version information and return it as tuple (release,
        versioninfo, machine) with versioninfo being a tuple (version,
        dev_stage, non_release_version).

        Entries which cannot be determined are set to the parameter values
        which default to ''. All tuple entries are strings.
    """
    info = _mac_ver_xml()
    if info is not None:
        return info
    return release, versioninfo, machine


def _java_getprop(name, default):
    from java.lang import System
    try:
        value = System.getProperty(name)
        if value is None:
            return default
        return value
    except AttributeError:
        return default


def java_ver(release='', vendor='', vminfo=('', '', ''), osinfo=('', '', '')):
    """ Version interface for Jython.

        Returns a tuple (release, vendor, vminfo, osinfo) with vminfo being
        a tuple (vm_name, vm_release, vm_vendor) and osinfo being a
        tuple (os_name, os_version, os_arch).

        Values which cannot be determined are set to the defaults
        given as parameters (which all default to '').

    """
    try:
        import java.lang
    except ImportError:
        return release, vendor, vminfo, osinfo
    vendor = _java_getprop('java.vendor', vendor)
    release = _java_getprop('java.version', release)
    vm_name, vm_release, vm_vendor = vminfo
    vm_name = _java_getprop('java.vm.name', vm_name)
    vm_vendor = _java_getprop('java.vm.vendor', vm_vendor)
    vm_release = _java_getprop('java.vm.version', vm_release)
    vminfo = vm_name, vm_release, vm_vendor
    os_name, os_version, os_arch = osinfo
    os_arch = _java_getprop('java.os.arch', os_arch)
    os_name = _java_getprop('java.os.name', os_name)
    os_version = _java_getprop('java.os.version', os_version)
    osinfo = os_name, os_version, os_arch
    return release, vendor, vminfo, osinfo


def system_alias(system, release, version):
    """ Returns (system, release, version) aliased to common
        marketing names used for some systems.

        It also does some reordering of the information in some cases
        where it would otherwise cause confusion.

    """
    if system == 'Rhapsody':
        return 'MacOS X Server', system + release, version
    elif system == 'SunOS':
        if release < '5':
            return system, release, version
        l = release.split('.')
        if l:
            try:
                major = int(l[0])
            except ValueError:
                pass
            else:
                major = major - 3
                l[0] = str(major)
                release = '.'.join(l)
        if release < '6':
            system = 'Solaris'
        else:
            system = 'Solaris'
    elif system == 'IRIX64':
        system = 'IRIX'
        if version:
            version = version + ' (64bit)'
        else:
            version = '64bit'
    elif system in ('win32', 'win16'):
        system = 'Windows'
    return system, release, version


def _platform(*args):
    """ Helper to format the platform string in a filename
        compatible format e.g. "system-version-machine".
    """
    platform = '-'.join(x.strip() for x in filter(len, args))
    platform = platform.replace(' ', '_')
    platform = platform.replace('/', '-')
    platform = platform.replace('\\', '-')
    platform = platform.replace(':', '-')
    platform = platform.replace(';', '-')
    platform = platform.replace('"', '-')
    platform = platform.replace('(', '-')
    platform = platform.replace(')', '-')
    platform = platform.replace('unknown', '')
    while 1:
        cleaned = platform.replace('--', '-')
        if cleaned == platform:
            break
        platform = cleaned
    while platform[-1] == '-':
        platform = platform[:-1]
    return platform


def _node(default=''):
    """ Helper to determine the node name of this machine.
    """
    try:
        import socket
    except ImportError:
        return default
    try:
        return socket.gethostname()
    except OSError:
        return default


def _follow_symlinks(filepath):
    """ In case filepath is a symlink, follow it until a
        real file is reached.
    """
    filepath = os.path.abspath(filepath)
    while os.path.islink(filepath):
        filepath = os.path.normpath(os.path.join(os.path.dirname(filepath),
            os.readlink(filepath)))
    return filepath


def _syscmd_uname(option, default=''):
    """ Interface to the system's uname command.
    """
    if sys.platform in ('dos', 'win32', 'win16'):
        return default
    try:
        f = os.popen('uname %s 2> %s' % (option, DEV_NULL))
    except (AttributeError, OSError):
        return default
    output = f.read().strip()
    rc = f.close()
    if not output or rc:
        return default
    else:
        return output


def _syscmd_file(target, default=''):
    """ Interface to the system's file command.

        The function uses the -b option of the file command to have it
        omit the filename in its output. Follow the symlinks. It returns
        default in case the command should fail.

    """
    if sys.platform in ('dos', 'win32', 'win16'):
        return default
    target = _follow_symlinks(target)
    try:
        proc = subprocess.Popen(['file', target], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
    except (AttributeError, OSError):
        return default
    output = proc.communicate()[0].decode('latin-1')
    rc = proc.wait()
    if not output or rc:
        return default
    else:
        return output


_default_architecture = {'win32': ('', 'WindowsPE'), 'win16': ('',
    'Windows'), 'dos': ('', 'MSDOS')}


def architecture(executable=sys.executable, bits='', linkage=''):
    """ Queries the given executable (defaults to the Python interpreter
        binary) for various architecture information.

        Returns a tuple (bits, linkage) which contains information about
        the bit architecture and the linkage format used for the
        executable. Both values are returned as strings.

        Values that cannot be determined are returned as given by the
        parameter presets. If bits is given as '', the sizeof(pointer)
        (or sizeof(long) on Python version < 1.5.2) is used as
        indicator for the supported pointer size.

        The function relies on the system's "file" command to do the
        actual work. This is available on most if not all Unix
        platforms. On some non-Unix platforms where the "file" command
        does not exist and the executable is set to the Python interpreter
        binary defaults from _default_architecture are used.

    """
    if not bits:
        import struct
        try:
            size = struct.calcsize('P')
        except struct.error:
            size = struct.calcsize('l')
        bits = str(size * 8) + 'bit'
    if executable:
        fileout = _syscmd_file(executable, '')
    else:
        fileout = ''
    if not fileout and executable == sys.executable:
        if sys.platform in _default_architecture:
            b, l = _default_architecture[sys.platform]
            if b:
                bits = b
            if l:
                linkage = l
        return bits, linkage
    if 'executable' not in fileout:
        return bits, linkage
    if '32-bit' in fileout:
        bits = '32bit'
    elif 'N32' in fileout:
        bits = 'n32bit'
    elif '64-bit' in fileout:
        bits = '64bit'
    if 'ELF' in fileout:
        linkage = 'ELF'
    elif 'PE' in fileout:
        if 'Windows' in fileout:
            linkage = 'WindowsPE'
        else:
            linkage = 'PE'
    elif 'COFF' in fileout:
        linkage = 'COFF'
    elif 'MS-DOS' in fileout:
        linkage = 'MSDOS'
    else:
        pass
    return bits, linkage


uname_result = collections.namedtuple('uname_result',
    'system node release version machine processor')
_uname_cache = None


def uname():
    """ Fairly portable uname interface. Returns a tuple
        of strings (system, node, release, version, machine, processor)
        identifying the underlying platform.

        Note that unlike the os.uname function this also returns
        possible processor information as an additional tuple entry.

        Entries which cannot be determined are set to ''.

    """
    global _uname_cache
    no_os_uname = 0
    if _uname_cache is not None:
        return _uname_cache
    processor = ''
    try:
        system, node, release, version, machine = os.uname()
    except AttributeError:
        no_os_uname = 1
    if no_os_uname or not list(filter(None, (system, node, release, version,
        machine))):
        if no_os_uname:
            system = sys.platform
            release = ''
            version = ''
            node = _node()
            machine = ''
        use_syscmd_ver = 1
        if system == 'win32':
            release, version, csd, ptype = win32_ver()
            if release and version:
                use_syscmd_ver = 0
            if not machine:
                if 'PROCESSOR_ARCHITEW6432' in os.environ:
                    machine = os.environ.get('PROCESSOR_ARCHITEW6432', '')
                else:
                    machine = os.environ.get('PROCESSOR_ARCHITECTURE', '')
            if not processor:
                processor = os.environ.get('PROCESSOR_IDENTIFIER', machine)
        if use_syscmd_ver:
            system, release, version = _syscmd_ver(system)
            if system == 'Microsoft Windows':
                system = 'Windows'
            elif system == 'Microsoft' and release == 'Windows':
                system = 'Windows'
                if '6.0' == version[:3]:
                    release = 'Vista'
                else:
                    release = ''
        if system in ('win32', 'win16'):
            if not version:
                if system == 'win32':
                    version = '32bit'
                else:
                    version = '16bit'
            system = 'Windows'
        elif system[:4] == 'java':
            release, vendor, vminfo, osinfo = java_ver()
            system = 'Java'
            version = ', '.join(vminfo)
            if not version:
                version = vendor
    if system == 'OpenVMS':
        if not release or release == '0':
            release = version
            version = ''
        try:
            import vms_lib
        except ImportError:
            pass
        else:
            csid, cpu_number = vms_lib.getsyi('SYI$_CPU', 0)
            if cpu_number >= 128:
                processor = 'Alpha'
            else:
                processor = 'VAX'
    if not processor:
        processor = _syscmd_uname('-p', '')
    if system == 'unknown':
        system = ''
    if node == 'unknown':
        node = ''
    if release == 'unknown':
        release = ''
    if version == 'unknown':
        version = ''
    if machine == 'unknown':
        machine = ''
    if processor == 'unknown':
        processor = ''
    if system == 'Microsoft' and release == 'Windows':
        system = 'Windows'
        release = 'Vista'
    _uname_cache = uname_result(system, node, release, version, machine,
        processor)
    return _uname_cache


def system():
    """ Returns the system/OS name, e.g. 'Linux', 'Windows' or 'Java'.

        An empty string is returned if the value cannot be determined.

    """
    return uname().system


def node():
    """ Returns the computer's network name (which may not be fully
        qualified)

        An empty string is returned if the value cannot be determined.

    """
    return uname().node


def release():
    """ Returns the system's release, e.g. '2.2.0' or 'NT'

        An empty string is returned if the value cannot be determined.

    """
    return uname().release


def version():
    """ Returns the system's release version, e.g. '#3 on degas'

        An empty string is returned if the value cannot be determined.

    """
    return uname().version


def machine():
    """ Returns the machine type, e.g. 'i386'

        An empty string is returned if the value cannot be determined.

    """
    return uname().machine


def processor():
    """ Returns the (true) processor name, e.g. 'amdk6'

        An empty string is returned if the value cannot be
        determined. Note that many platforms do not provide this
        information or simply return the same value as for machine(),
        e.g.  NetBSD does this.

    """
    return uname().processor


_sys_version_parser = re.compile(
    '([\\w.+]+)\\s*\\(#?([^,]+)(?:,\\s*([\\w ]*)(?:,\\s*([\\w :]*))?)?\\)\\s*\\[([^\\]]+)\\]?'
    , re.ASCII)
_ironpython_sys_version_parser = re.compile(
    'IronPython\\s*([\\d\\.]+)(?: \\(([\\d\\.]+)\\))? on (.NET [\\d\\.]+)',
    re.ASCII)
_ironpython26_sys_version_parser = re.compile(
    '([\\d.]+)\\s*\\(IronPython\\s*[\\d.]+\\s*\\(([\\d.]+)\\) on ([\\w.]+ [\\d.]+(?: \\(\\d+-bit\\))?)\\)'
    )
_pypy_sys_version_parser = re.compile(
    '([\\w.+]+)\\s*\\(#?([^,]+),\\s*([\\w ]+),\\s*([\\w :]+)\\)\\s*\\[PyPy [^\\]]+\\]?'
    )
_sys_version_cache = {}


def _sys_version(sys_version=None):
    """ Returns a parsed version of Python's sys.version as tuple
        (name, version, branch, revision, buildno, builddate, compiler)
        referring to the Python implementation name, version, branch,
        revision, build number, build date/time as string and the compiler
        identification string.

        Note that unlike the Python sys.version, the returned value
        for the Python version will always include the patchlevel (it
        defaults to '.0').

        The function returns empty strings for tuple entries that
        cannot be determined.

        sys_version may be given to parse an alternative version
        string, e.g. if the version was read from a different Python
        interpreter.

    """
    if sys_version is None:
        sys_version = sys.version
    result = _sys_version_cache.get(sys_version, None)
    if result is not None:
        return result
    if 'IronPython' in sys_version:
        name = 'IronPython'
        if sys_version.startswith('IronPython'):
            match = _ironpython_sys_version_parser.match(sys_version)
        else:
            match = _ironpython26_sys_version_parser.match(sys_version)
        if match is None:
            raise ValueError('failed to parse IronPython sys.version: %s' %
                repr(sys_version))
        version, alt_version, compiler = match.groups()
        buildno = ''
        builddate = ''
    elif sys.platform.startswith('java'):
        name = 'Jython'
        match = _sys_version_parser.match(sys_version)
        if match is None:
            raise ValueError('failed to parse Jython sys.version: %s' %
                repr(sys_version))
        version, buildno, builddate, buildtime, _ = match.groups()
        if builddate is None:
            builddate = ''
        compiler = sys.platform
    elif 'PyPy' in sys_version:
        name = 'PyPy'
        match = _pypy_sys_version_parser.match(sys_version)
        if match is None:
            raise ValueError('failed to parse PyPy sys.version: %s' % repr(
                sys_version))
        version, buildno, builddate, buildtime = match.groups()
        compiler = ''
    else:
        match = _sys_version_parser.match(sys_version)
        if match is None:
            raise ValueError('failed to parse CPython sys.version: %s' %
                repr(sys_version))
        version, buildno, builddate, buildtime, compiler = match.groups()
        name = 'CPython'
        if builddate is None:
            builddate = ''
        elif buildtime:
            builddate = builddate + ' ' + buildtime
    if hasattr(sys, '_git'):
        _, branch, revision = sys._git
    elif hasattr(sys, '_mercurial'):
        _, branch, revision = sys._mercurial
    elif hasattr(sys, 'subversion'):
        _, branch, revision = sys.subversion
    else:
        branch = ''
        revision = ''
    l = version.split('.')
    if len(l) == 2:
        l.append('0')
        version = '.'.join(l)
    result = name, version, branch, revision, buildno, builddate, compiler
    _sys_version_cache[sys_version] = result
    return result


def python_implementation():
    """ Returns a string identifying the Python implementation.

        Currently, the following implementations are identified:
          'CPython' (C implementation of Python),
          'IronPython' (.NET implementation of Python),
          'Jython' (Java implementation of Python),
          'PyPy' (Python implementation of Python).

    """
    return _sys_version()[0]


def python_version():
    """ Returns the Python version as string 'major.minor.patchlevel'

        Note that unlike the Python sys.version, the returned value
        will always include the patchlevel (it defaults to 0).

    """
    return _sys_version()[1]


def python_version_tuple():
    """ Returns the Python version as tuple (major, minor, patchlevel)
        of strings.

        Note that unlike the Python sys.version, the returned value
        will always include the patchlevel (it defaults to 0).

    """
    return tuple(_sys_version()[1].split('.'))


def python_branch():
    """ Returns a string identifying the Python implementation
        branch.

        For CPython this is the Subversion branch from which the
        Python binary was built.

        If not available, an empty string is returned.

    """
    return _sys_version()[2]


def python_revision():
    """ Returns a string identifying the Python implementation
        revision.

        For CPython this is the Subversion revision from which the
        Python binary was built.

        If not available, an empty string is returned.

    """
    return _sys_version()[3]


def python_build():
    """ Returns a tuple (buildno, builddate) stating the Python
        build number and date as strings.

    """
    return _sys_version()[4:6]


def python_compiler():
    """ Returns a string identifying the compiler used for compiling
        Python.

    """
    return _sys_version()[6]


_platform_cache = {}


def platform(aliased=0, terse=0):
    """ Returns a single string identifying the underlying platform
        with as much useful information as possible (but no more :).

        The output is intended to be human readable rather than
        machine parseable. It may look different on different
        platforms and this is intended.

        If "aliased" is true, the function will use aliases for
        various platforms that report system names which differ from
        their common names, e.g. SunOS will be reported as
        Solaris. The system_alias() function is used to implement
        this.

        Setting terse to true causes the function to return only the
        absolute minimum information needed to identify the platform.

    """
    result = _platform_cache.get((aliased, terse), None)
    if result is not None:
        return result
    system, node, release, version, machine, processor = uname()
    if machine == processor:
        processor = ''
    if aliased:
        system, release, version = system_alias(system, release, version)
    if system == 'Windows':
        rel, vers, csd, ptype = win32_ver(version)
        if terse:
            platform = _platform(system, release)
        else:
            platform = _platform(system, release, version, csd)
    elif system in ('Linux',):
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',
                'dist\\(\\) and linux_distribution\\(\\) functions are deprecated .*'
                , PendingDeprecationWarning)
            distname, distversion, distid = dist('')
        if distname and not terse:
            platform = _platform(system, release, machine, processor,
                'with', distname, distversion, distid)
        else:
            libcname, libcversion = libc_ver(sys.executable)
            platform = _platform(system, release, machine, processor,
                'with', libcname + libcversion)
    elif system == 'Java':
        r, v, vminfo, (os_name, os_version, os_arch) = java_ver()
        if terse or not os_name:
            platform = _platform(system, release, version)
        else:
            platform = _platform(system, release, version, 'on', os_name,
                os_version, os_arch)
    elif system == 'MacOS':
        if terse:
            platform = _platform(system, release)
        else:
            platform = _platform(system, release, machine)
    elif terse:
        platform = _platform(system, release)
    else:
        bits, linkage = architecture(sys.executable)
        platform = _platform(system, release, machine, processor, bits, linkage
            )
    _platform_cache[aliased, terse] = platform
    return platform


if __name__ == '__main__':
    terse = 'terse' in sys.argv or '--terse' in sys.argv
    aliased = not 'nonaliased' in sys.argv and not '--nonaliased' in sys.argv
    print(platform(aliased, terse))
    sys.exit(0)
