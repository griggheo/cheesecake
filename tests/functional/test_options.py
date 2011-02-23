
import os
import tempfile

from _helper_cheesecake import FunctionalTest, read_file_contents, NOSE_PATH, PACKAGE_PATH

from cheesecake.util import pad_msg
from cheesecake.cheesecake_index import IndexUnpack
from cheesecake.cheesecake_index import IndexUnpackDir
from cheesecake.cheesecake_index import IndexInstall
from cheesecake.cheesecake_index import IndexUrlDownload
from cheesecake.cheesecake_index import IndexPyPIDownload


class TestOptions(FunctionalTest):
    def test_no_args(self):
        self._run_cheesecake('')

        assert self.return_code != 0

        # Make sure that there's a reference to --help.
        stdout = read_file_contents(self.stdout_name)
        assert '--help' in stdout

    def test_help(self):
        self._run_cheesecake('--help')

        self._assert_success()

        # Make sure usage information has been shown.
        stdout = read_file_contents(self.stdout_name)
        assert 'usage:' in stdout

    def test_name(self):
        self._run_cheesecake('--name nose')

        self._assert_success()

        # Make sure that appropriate indices have been counted.
        stdout = read_file_contents(self.stdout_name)
        assert pad_msg('unpack', IndexUnpack.max_value) in stdout
        assert pad_msg('install', IndexInstall.max_value) in stdout
        # PyPI score can be lowered by penalties, so we don't include score check here.
        assert 'py_pi_download' in stdout

    def test_url(self):
        self._run_cheesecake('--url http://www.agilistas.org/cheesecake/nose-0.8.3.tar.gz')

        self._assert_success()

        # Make sure that appropriate indices have been counted.
        stdout = read_file_contents(self.stdout_name)
        assert pad_msg('unpack', IndexUnpack.max_value) in stdout
        assert pad_msg('unpack_dir', IndexUnpackDir.max_value) in stdout
        assert pad_msg('install', IndexInstall.max_value) in stdout
        assert pad_msg('url_download', IndexUrlDownload.max_value) in stdout

    def test_path(self):
        self._run_cheesecake('--path %s' % NOSE_PATH)

        self._assert_success()

        # Make sure that appropriate indices have been counted.
        stdout = read_file_contents(self.stdout_name)
        assert pad_msg('unpack', IndexUnpack.max_value) in stdout
        assert pad_msg('unpack_dir', IndexUnpackDir.max_value) in stdout
        assert pad_msg('install', IndexInstall.max_value) in stdout

    def test_verbose(self):
        self._run_cheesecake('--path %s' % PACKAGE_PATH)
        normal = read_file_contents(self.stdout_name)
        self._cleanup()

        self._run_cheesecake('--path %s --verbose' % PACKAGE_PATH)
        verbose = read_file_contents(self.stdout_name)

        # Make sure that --verbose generates more information than default operation.
        assert len(verbose) > len(normal)

    def test_quiet(self):
        self._run_cheesecake('--path %s' % PACKAGE_PATH)
        normal = read_file_contents(self.stdout_name)
        self._cleanup()

        self._run_cheesecake('--path %s --quiet' % PACKAGE_PATH)
        quiet = read_file_contents(self.stdout_name)

        # Make sure that --quiet generates less information than default operation.
        assert len(quiet) < len(normal)

    def test_keep_log(self):
        logfile = tempfile.mktemp(prefix='log')
        self._run_cheesecake('--path %s --logfile %s --keep-log' % (NOSE_PATH, logfile))

        self._assert_success()

        # Make sure that log file was left.
        assert os.path.exists(logfile)

        # Delete the logfile now.
        os.unlink(logfile)
