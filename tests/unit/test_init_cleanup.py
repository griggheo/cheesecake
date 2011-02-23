import os
import shutil
import tempfile

import _path_cheesecake
from _helper_cheesecake import DATA_PATH
from cheesecake.cheesecake_index import Cheesecake
from cheesecake.util import rmtree


class TestInitCleanup(object):
    def tearDown(self):
        if hasattr(self, 'cheesecake'):
            if os.path.isdir(self.cheesecake.sandbox):
                rmtree(self.cheesecake.sandbox)
        if hasattr(self, 'logfile'):
            if os.path.isfile(self.logfile):
                os.unlink(self.logfile)

    def test_init(self):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "package1.tar.gz"))
        assert os.path.isdir(self.cheesecake.sandbox_pkg_dir)
        assert os.path.isfile(self.cheesecake.sandbox_pkg_file)
        self.logfile = self.cheesecake.logfile
        assert os.path.isfile(self.logfile)

    def test_init_custom_logfile(self):
        self.logfile = tempfile.mktemp()
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "package1.tar.gz"),
                                     logfile=self.logfile)
        assert os.path.isdir(self.cheesecake.sandbox_pkg_dir)
        assert os.path.isfile(self.cheesecake.sandbox_pkg_file)
        assert os.path.isfile(self.logfile)

    def test_cleanup_after_install(self):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "package1.tar.gz"))
        self.cheesecake.cleanup()
        assert not os.path.exists(self.cheesecake.sandbox_pkg_dir)
        assert not os.path.exists(self.cheesecake.sandbox_pkg_file)
        assert not os.path.exists(self.cheesecake.sandbox_install_dir)
        assert not os.path.exists(self.cheesecake.sandbox)
        self.logfile = self.cheesecake.logfile
        assert not os.path.isfile(self.logfile)
