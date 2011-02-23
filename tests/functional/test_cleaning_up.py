from glob import glob
import os
import tempfile

from _helper_cheesecake import FunctionalTest, read_file_contents, NOSE_PATH, INVALID_PACKAGE_PATH


def filter_our_files(files):
    uid = os.getuid()
    return filter(lambda filename: os.lstat(filename).st_uid == uid, files)

def get_tmp_files_starting_with(prefix):
    return glob(os.path.join(tempfile.gettempdir(), prefix + "*"))

def get_tmp_files():
    return get_tmp_files_starting_with(tempfile.gettempprefix())

def get_cheesecake_files():
    return get_tmp_files_starting_with("cheesecake")


class TestCleaningUp(FunctionalTest):
    def setUp(self):
        self.temp_files = filter_our_files(get_tmp_files())
        self.cheesecake_files = filter_our_files(get_cheesecake_files())
        self.sandbox = tempfile.mkdtemp()
        self.logfile = tempfile.mktemp(prefix='log')

    def test_valid_no_tmp(self):
        "Check that no files are left in temp by Cheesecake."
        self._run_cheesecake('-p %s -s %s -l %s' % (NOSE_PATH, self.sandbox, self.logfile))

        self._assert_success()

        # Check that Cheesecake didn't leave sandbox.
        assert not os.path.exists(self.sandbox)

        # Check that log file has been removed.
        assert not os.path.exists(self.logfile)

        # Check that Cheesecake didn't leave any cheesecake* files.
        assert filter_our_files(get_cheesecake_files()) == self.cheesecake_files

        # Check that Cheesecake didn't leave any new tmp* files.
        assert filter_our_files(get_tmp_files()) == self.temp_files

    def test_invalid_no_tmp(self):
        "Check that no files are left in temp by Cheesecake during scoring an invalid package."
        self._run_cheesecake('-p %s -s %s -l %s' % (INVALID_PACKAGE_PATH, self.sandbox, self.logfile))

        # Package cannot be unpacked, but error was handled and scores, so no error here.
        self._assert_success()

        # Check that Cheesecake didn't leave sandbox.
        assert not os.path.exists(self.sandbox)

        # Check that Cheesecake didn't leave any cheesecake* files.
        assert filter_our_files(get_cheesecake_files()) == self.cheesecake_files

        # Check that Cheesecake didn't leave any new tmp* files.
        assert filter_our_files(get_tmp_files()) == self.temp_files

        # Delete the log file, so that it doesn't pollute /tmp
        self._cleanup_logfile()

    def _cleanup_logfile(self):
        os.unlink(self.logfile)
