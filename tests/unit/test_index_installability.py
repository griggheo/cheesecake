import os

import _path_cheesecake
from _helper_cheesecake import SAMPLE_PACKAGE_PATH, SAMPLE_PACKAGE_URL
from _helper_cheesecake import mocked_urlretrieve

import cheesecake.cheesecake_index as cheesecake_index
from cheesecake.cheesecake_index import Cheesecake
from cheesecake.cheesecake_index import IndexPyPIDownload
from cheesecake.cheesecake_index import IndexUnpack
from cheesecake.cheesecake_index import IndexUnpackDir
from cheesecake.cheesecake_index import IndexSetupPy
from cheesecake.cheesecake_index import IndexInstall
from cheesecake.cheesecake_index import IndexUrlDownload
from cheesecake.cheesecake_index import IndexGeneratedFiles


class TestIndexInstallability(object):
    def setUp(self):
        self.cheesecake = None
        cheesecake_index.urlretrieve = mocked_urlretrieve

    def tearDown(self):
        if not self.cheesecake:
            return
        self.cheesecake.cleanup()

    def test_index_installability_local_path(self):
        self.cheesecake = Cheesecake(path=SAMPLE_PACKAGE_PATH)

        index = self.cheesecake.index["INSTALLABILITY"]
        parts = [IndexUnpack, IndexUnpackDir, IndexSetupPy, IndexInstall, IndexGeneratedFiles]

        assert index.max_value == sum(map(lambda x: x.max_value, parts))

        index.compute_with(self.cheesecake)
        assert index.value == sum(map(lambda x: x.max_value, parts))

    def test_index_installability_url_download(self):
        self.cheesecake = Cheesecake(url=SAMPLE_PACKAGE_URL)

        index = self.cheesecake.index["INSTALLABILITY"]
        parts = [IndexUrlDownload, IndexUnpack, IndexUnpackDir, IndexSetupPy, IndexInstall, IndexGeneratedFiles]

        assert index.max_value == sum(map(lambda x: x.max_value, parts))

        index.compute_with(self.cheesecake)
        assert index.value == sum(map(lambda x: x.max_value, parts))
