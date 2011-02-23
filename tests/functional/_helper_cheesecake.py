import os
import sys
import tempfile

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(current_dir, '../../'))

try:
    import subprocess
except ImportError, ex:
    from cheesecake import subprocess


CHEESECAKE_PATH = os.path.abspath(os.path.join(current_dir,
                                               '../../cheesecake_index'))
DATA_PATH = os.path.abspath(os.path.join(current_dir, '../data/'))
NOSE_PATH = os.path.join(DATA_PATH, 'nose-0.8.3.tar.gz')
PACKAGE_PATH = os.path.join(DATA_PATH, 'package2.tar.gz')
INVALID_PACKAGE_PATH = os.path.join(DATA_PATH, 'invalid_package.tar.gz')


class FunctionalTest(object):
    def _run_cheesecake(self, arguments):
        self.stdout_fd, self.stdout_name = tempfile.mkstemp(prefix='functional') 
        self.stderr_fd, self.stderr_name = tempfile.mkstemp(prefix='functional')
        self.process = subprocess.Popen('%s %s' % (CHEESECAKE_PATH, arguments),
                         stdout=self.stdout_fd,
                         stderr=self.stderr_fd,
                         shell=True)
        self.return_code = self.process.wait()

    def _assert_success(self):
        # Check that Cheesecake exited sucessfully.
        print "Return code: %d" % self.return_code
        assert self.return_code == 0

        # Check that Cheesecake didn't wrote anything into stderr.
        stderr_contents = read_file_contents(self.stderr_name)
        print "Stderr contents:\n***\n%s\n***\n" % stderr_contents
        assert stderr_contents == ''

    def _cleanup(self):
        os.unlink(self.stdout_name)
        os.unlink(self.stderr_name)

    def tearDown(self):
        self._cleanup()


def read_file_contents(filename):
    fd = file(filename)

    contents = fd.read()
    fd.close()

    return contents
