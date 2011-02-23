"""Utility functions for Cheesecake project.
"""

import os
import shutil
import signal
import stat
import sys
import tarfile
import tempfile
import time
import zipfile

from subprocess import call, ProcessError, Popen, PIPE, STDOUT

PAD_TEXT = 40
PAD_VALUE = 4

def make_temp_file():
    tmpfd, tmpname = tempfile.mkstemp()
    return os.fdopen(tmpfd, 'w+'), tmpname

def run_cmd(cmd, env=None, max_timeout=None):
    """Run command and return its return code and its output.

    >>> run_cmd('/bin/true')
    (0, '')

    >>> run_cmd('/bin/cat', max_timeout=0.2)
    (1, 'Time exceeded')
    """
    arglist = cmd.split()
    output, output_name = make_temp_file()

    try:
        try:
            p = Popen(arglist, stdout=output, stderr=STDOUT, env=env)

            # Wait only max_timeout seconds.
            if max_timeout:
                start = time.time()
                while p.poll() is None:
                    time.sleep(0.1)
                    if time.time() - start > max_timeout:
                        os.kill(p.pid, signal.SIGINT)
                        p.wait()
                        return 1, "Time exceeded"

            p.wait()
            output.seek(0)

            output_content = output.read()

            return p.returncode, output_content
        except Exception, e:
            return 1, e
    finally:
        output.close()
        os.unlink(output_name)

def command_successful(cmd):
    """Returns True if command exited normally, False otherwise.

    >>> command_successful('/bin/true')
    True
    >>> command_successful('this-command-doesnt-exist')
    False
    """
    rc, output = run_cmd(cmd)
    return rc == 0

class StdoutRedirector(object):
    """Redirect stdout to a temporary file.
    """
    def __init__(self, filename=None):
        if filename:
            self.fh = open(filename, 'w')
            self.fname = None
        else:
            self.fh, self.fname = make_temp_file()

    def write(self, buf):
        self.fh.write(buf)

    def flush(self):
        self.fh.flush()

    def read_buffer(self):
        """Return contents of the temporary file.
        """
        self.fh.seek(0)

        output = self.fh.read()
        self.fh.close()
        if self.fname:
            os.unlink(self.fname)

        return output

def pad_with_dots(msg, length=PAD_TEXT):
    """Pad text with dots up to given length.

    >>> pad_with_dots("Hello world", 20)
    'Hello world ........'
    >>> pad_with_dots("Exceeding length", 10)
    'Exceeding length'
    """
    msg_length = len(msg)

    if msg_length >= length:
        return msg

    msg = msg + " "
    for i in range(msg_length+1, length):
        msg += "."
    return msg

def pad_left_spaces(value, length=PAD_VALUE):
    """Pad value with spaces at left up to given length.

    >>> pad_left_spaces(15, 4)
    '  15'
    >>> pad_left_spaces(123456, 2)
    '123456'
    >>> len(pad_left_spaces("")) == PAD_VALUE
    True
    """
    if not isinstance(value, basestring):
        value = str(value)
    diff = length - len(value)
    return " " * diff + value

def pad_right_spaces(value, length=PAD_VALUE):
    """Pad value with spaces at left up to given length.

    >>> pad_right_spaces(123, 5)
    '123  '
    >>> pad_right_spaces(12.1, 5)
    '12.1 '
    """
    if not isinstance(value, basestring):
        value = str(value)
    diff = length - len(value)
    return value + " " * diff

def pad_msg(msg, value, msg_length=PAD_TEXT, value_length=PAD_VALUE):
    """Pad message with dots and pad value with spaces.

    >>> pad_msg("123456", 77, msg_length=10, value_length=4)
    '123456 ...  77'
    >>> pad_msg("123", u"45", msg_length=5, value_length=3)
    u'123 . 45'
    """
    return msg + " " +"." * (msg_length-len(msg)-1) + pad_left_spaces(value, value_length)

def pad_line(char="=", length=(PAD_TEXT+PAD_VALUE+1)):
    """Return line consisting of 'char' characters.

    >>> pad_line('*', 3)
    '***'
    >>> pad_line(length=10)
    '=========='
    """
    return char * length

def unzip_package(package, destination):
    """Unzip given `package` to the `destination` directory.

    Return name of unpacked directory or None on error.
    """
    try:
        z = zipfile.ZipFile(package)
    except zipfile.error:
        return None

    # Get directory structure from zip and create it in destination directory.
    for name in z.namelist():
        (dir, file) = os.path.split(name)
        unpack_dir = dir
        target_dir = os.path.join(destination, dir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

    # Extract files to directory structure
    for i, name in enumerate(z.namelist()):
        if not name.endswith('/'):
            outfile = open(os.path.join(destination, name), 'wb')
            outfile.write(z.read(name))
            outfile.flush()
            outfile.close()

    return unpack_dir.split("/")[0]

def untar_package(package, destination):
    """Untar given `package` to the `destination` directory.

    Return name of unpacked directory or None on error.
    """
    try:
        t = tarfile.open(package)
    except tarfile.ReadError, e:
        return None

    for member in t.getmembers():
        t.extract(member, destination)

    tarinfo = t.members[0]
    t.close()

    ## GG: os.sep is \\ when running cheesecake on Windows
    ## while inside the tar.gz the separator is /
    ## We use / because most tar.gz archives are created on *nix
    ##return tarinfo.name.split(os.sep)[0]
    return tarinfo.name.split('/')[0]

def unegg_package(package, destination):
    """Unpack given egg to the `destination` directory.

    Return name of unpacked directory or None on error.
    """
    if os.path.isdir(package):
        package_name = os.path.basename(package)
        destination = os.path.join(destination, package_name)
        shutil.copytree(package, destination, symlinks=True)
        return package_name
    else:
        return unzip_package(package, destination)

def mkdirs(dir):
    """Make directory with parent directories as needed.

    Don't throw an exception if directory exists.
    """
    parts = dir.split(os.path.sep)
    for length in xrange(1, len(parts)+1):
        path = os.path.sep.join([''] + parts[:length])
        if not os.path.exists(path):
            os.mkdir(path)

def time_function(function):
    """Measure function execution time.

    Return (return value, time taken) tuple.

    >>> def fun(x):
    ...     return x*2
    >>> ret, time_taken = time_function(lambda: fun(5))
    >>> ret
    10
    """
    start = time.time()
    ret = function()
    end = time.time()
    return ret, end-start

def rmtree(topdir):
    """Remove the whole directory tree (including subdirectories).

    Works around some Windows-specific behaviour of shutil.rmtree.
    """
    all_privileges = stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC

    # Make all files and diretories writable.
    os.chmod(topdir, all_privileges)
    for root, dirnames, filenames in os.walk(topdir):
        for name in dirnames + filenames:
            try:
                os.chmod(os.path.join(root, name), all_privileges)
            except OSError:
                pass

    shutil.rmtree(topdir, ignore_errors=True)

