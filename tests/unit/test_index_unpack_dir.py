import os

import _path_cheesecake
from _helper_cheesecake import DATA_PATH
from cheesecake.cheesecake_index import Cheesecake, IndexUnpackDir


class IndexUnpackDirTest(object):
    def setUp(self):
        self.cheesecake = None

    def tearDown(self):
        if not self.cheesecake:
            return
        self.cheesecake.cleanup()

class TestIndexUnpackDirCorrectPackage(IndexUnpackDirTest):
    def test_index_unpack_dir_correct_package(self):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "package1.tar.gz"))
        index = self.cheesecake.index["INSTALLABILITY"]["IndexUnpackDir"]

        index.compute_with(self.cheesecake)

        assert index.name == "IndexUnpackDir"
        assert index.value == IndexUnpackDir.max_value
        assert index.details == "unpack directory is " + self.cheesecake.package_name + " as expected"

class TestIndexUnpackDirCorrectPackage(IndexUnpackDirTest):
    def test_index_unpack_dir_incorrect_package(self):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "package_renamed.tar.gz"))
        index = self.cheesecake.index["INSTALLABILITY"]["IndexUnpackDir"]

        index.compute_with(self.cheesecake)

        assert index.name == "IndexUnpackDir"
        print index.value, index.max_value
        assert index.value == 0
        assert index.details == "unpack directory is package1 instead of the expected package_renamed"
