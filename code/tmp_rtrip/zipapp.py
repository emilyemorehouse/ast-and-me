import contextlib
import os
import pathlib
import shutil
import stat
import sys
import zipfile
__all__ = ['ZipAppError', 'create_archive', 'get_interpreter']
MAIN_TEMPLATE = """# -*- coding: utf-8 -*-
import {module}
{module}.{fn}()
"""
if sys.platform.startswith('win'):
    shebang_encoding = 'utf-8'
else:
    shebang_encoding = sys.getfilesystemencoding()


class ZipAppError(ValueError):
    pass


@contextlib.contextmanager
def _maybe_open(archive, mode):
    if isinstance(archive, pathlib.Path):
        archive = str(archive)
    if isinstance(archive, str):
        with open(archive, mode) as f:
            yield f
    else:
        yield archive


def _write_file_prefix(f, interpreter):
    """Write a shebang line."""
    if interpreter:
        shebang = b'#!' + interpreter.encode(shebang_encoding) + b'\n'
        f.write(shebang)


def _copy_archive(archive, new_archive, interpreter=None):
    """Copy an application archive, modifying the shebang line."""
    with _maybe_open(archive, 'rb') as src:
        first_2 = src.read(2)
        if first_2 == b'#!':
            first_2 = b''
            src.readline()
        with _maybe_open(new_archive, 'wb') as dst:
            _write_file_prefix(dst, interpreter)
            dst.write(first_2)
            shutil.copyfileobj(src, dst)
    if interpreter and isinstance(new_archive, str):
        os.chmod(new_archive, os.stat(new_archive).st_mode | stat.S_IEXEC)


def create_archive(source, target=None, interpreter=None, main=None):
    """Create an application archive from SOURCE.

    The SOURCE can be the name of a directory, or a filename or a file-like
    object referring to an existing archive.

    The content of SOURCE is packed into an application archive in TARGET,
    which can be a filename or a file-like object.  If SOURCE is a directory,
    TARGET can be omitted and will default to the name of SOURCE with .pyz
    appended.

    The created application archive will have a shebang line specifying
    that it should run with INTERPRETER (there will be no shebang line if
    INTERPRETER is None), and a __main__.py which runs MAIN (if MAIN is
    not specified, an existing __main__.py will be used).  It is an error
    to specify MAIN for anything other than a directory source with no
    __main__.py, and it is an error to omit MAIN if the directory has no
    __main__.py.
    """
    source_is_file = False
    if hasattr(source, 'read') and hasattr(source, 'readline'):
        source_is_file = True
    else:
        source = pathlib.Path(source)
        if source.is_file():
            source_is_file = True
    if source_is_file:
        _copy_archive(source, target, interpreter)
        return
    if not source.exists():
        raise ZipAppError('Source does not exist')
    has_main = (source / '__main__.py').is_file()
    if main and has_main:
        raise ZipAppError(
            'Cannot specify entry point if the source has __main__.py')
    if not (main or has_main):
        raise ZipAppError('Archive has no entry point')
    main_py = None
    if main:
        mod, sep, fn = main.partition(':')
        mod_ok = all(part.isidentifier() for part in mod.split('.'))
        fn_ok = all(part.isidentifier() for part in fn.split('.'))
        if not (sep == ':' and mod_ok and fn_ok):
            raise ZipAppError('Invalid entry point: ' + main)
        main_py = MAIN_TEMPLATE.format(module=mod, fn=fn)
    if target is None:
        target = source.with_suffix('.pyz')
    elif not hasattr(target, 'write'):
        target = pathlib.Path(target)
    with _maybe_open(target, 'wb') as fd:
        _write_file_prefix(fd, interpreter)
        with zipfile.ZipFile(fd, 'w') as z:
            root = pathlib.Path(source)
            for child in root.rglob('*'):
                arcname = str(child.relative_to(root))
                z.write(str(child), arcname)
            if main_py:
                z.writestr('__main__.py', main_py.encode('utf-8'))
    if interpreter and not hasattr(target, 'write'):
        target.chmod(target.stat().st_mode | stat.S_IEXEC)


def get_interpreter(archive):
    with _maybe_open(archive, 'rb') as f:
        if f.read(2) == b'#!':
            return f.readline().strip().decode(shebang_encoding)


def main(args=None):
    """Run the zipapp command line interface.

    The ARGS parameter lets you specify the argument list directly.
    Omitting ARGS (or setting it to None) works as for argparse, using
    sys.argv[1:] as the argument list.
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', default=None, help=
        'The name of the output archive. Required if SOURCE is an archive.')
    parser.add_argument('--python', '-p', default=None, help=
        'The name of the Python interpreter to use (default: no shebang line).'
        )
    parser.add_argument('--main', '-m', default=None, help=
        'The main function of the application (default: use an existing __main__.py).'
        )
    parser.add_argument('--info', default=False, action='store_true', help=
        'Display the interpreter from the archive.')
    parser.add_argument('source', help=
        'Source directory (or existing archive).')
    args = parser.parse_args(args)
    if args.info:
        if not os.path.isfile(args.source):
            raise SystemExit('Can only get info for an archive file')
        interpreter = get_interpreter(args.source)
        print('Interpreter: {}'.format(interpreter or '<none>'))
        sys.exit(0)
    if os.path.isfile(args.source):
        if args.output is None or os.path.exists(args.output
            ) and os.path.samefile(args.source, args.output):
            raise SystemExit('In-place editing of archives is not supported')
        if args.main:
            raise SystemExit('Cannot change the main function when copying')
    create_archive(args.source, args.output, interpreter=args.python, main=
        args.main)


if __name__ == '__main__':
    main()
