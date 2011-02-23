import os
import tempfile

import _path_cheesecake
from _helper_cheesecake import DATA_PATH
from cheesecake.cheesecake_index import Cheesecake, CheesecakeError, pad_msg

default_temp_directory = os.path.join(tempfile.gettempdir(), 'cheesecake_sandbox')

class TestIndexUnpack(object):
    def setUp(self):
        self.cheesecake = None
        self.logfile = None

    def tearDown(self):
        if self.cheesecake:
            self.cheesecake.cleanup()

        if self.logfile:
            os.unlink(self.logfile)

    def _run_valid(self, package_file):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, package_file))

        index = self.cheesecake.index["INSTALLABILITY"]["IndexUnpack"]
        index.compute_with(self.cheesecake)

        assert index.name == "IndexUnpack"
        assert index.value == index.max_value
        assert index.details == "package unpacked successfully"

    def test_index_unpack_valid_tar_gz(self):
        self._run_valid("package1.tar.gz")

    def test_index_unpack_valid_tgz(self):
        self._run_valid("package1.tgz")

    def test_index_unpack_valid_zip(self):
        self._run_valid("package1.zip")

    def _run_invalid(self, package_file):
        self.logfile = tempfile.mktemp()

        try:
            self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, package_file),
                                         sandbox=default_temp_directory,
                                         logfile=self.logfile)
            assert 0 # This statement should not be reached
        except CheesecakeError, e:
            msg = "Error: Could not unpack package %s ... exiting" % \
                  os.path.join(default_temp_directory, package_file)
            msg += "\nDetailed info available in log file %s" % self.logfile
            assert str(e) == msg

            # If run failed log file should not be deleted.
            assert os.path.isfile(self.logfile)

    def test_index_unpack_invalid_tar_gz(self):
        self._run_invalid("invalid_package.tar.gz")

    def test_index_unpack_invalid_tgz(self):
        self._run_invalid("invalid_package.tgz")

    def test_index_unpack_invalid_zip(self):
        self._run_invalid("invalid_package.zip")
