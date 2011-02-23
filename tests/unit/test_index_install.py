import os

import _path_cheesecake
from _helper_cheesecake import DATA_PATH
from cheesecake.cheesecake_index import Cheesecake


class TestIndexInstall(object):
    def setUp(self):
        self.cheesecake = None

    def tearDown(self):
        if not self.cheesecake:
            return
        self.cheesecake.cleanup()

    def test_index_install_correct_package(self):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "nose-0.8.3.tar.gz"))

        index = self.cheesecake.index["INSTALLABILITY"]["IndexInstall"]
        index.compute_with(self.cheesecake)

        assert index.name == "IndexInstall"
        assert index.value == index.max_value
        assert index.details == "package installed in " + self.cheesecake.sandbox_install_dir

    def test_index_install_incorrect_package(self):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "package1.tar.gz"))

        index = self.cheesecake.index["INSTALLABILITY"]["IndexInstall"]
        index.compute_with(self.cheesecake)

        assert index.name == "IndexInstall"
        assert index.value == 0
        assert index.details == "could not install package in " + self.cheesecake.sandbox_install_dir
