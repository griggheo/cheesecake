
import os
import tempfile

from _helper_cheesecake import FunctionalTest, read_file_contents, PACKAGE_PATH, INVALID_PACKAGE_PATH


class TestLogfile(FunctionalTest):
    def setUp(self):
        self.logfile = tempfile.mktemp(prefix='log')

    def tearDown(self):
        super(self.__class__, self).tearDown()
        if os.path.exists(self.logfile):
            os.unlink(self.logfile)

    def test_valid_package(self):
        self._run_cheesecake('--path %s --logfile %s' % \
                             (PACKAGE_PATH, self.logfile))

        self._assert_success()

        # After successful installation there's no need to keep a logfile.
        assert not os.path.exists(self.logfile)

    def test_broken_package(self):
        self._run_cheesecake('--path %s --logfile %s' % \
                             (INVALID_PACKAGE_PATH, self.logfile))

        # Package is broken, but error was handled.
        self._assert_success()

        # Unpacking failed - logfile should have been left.
        assert os.path.exists(self.logfile)
