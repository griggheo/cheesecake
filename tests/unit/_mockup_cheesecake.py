
import os
import shutil
import tempfile

import _path_cheesecake
from cheesecake.cheesecake_index import Cheesecake
from cheesecake.cheesecake_index import CheesecakeIndex
from cheesecake.util import rmtree

from _helper_cheesecake import create_empty_files_in_directory


class MockupCheesecakeTest(object):
    project_name = 'test_project'

    class CheesecakeMockup(Cheesecake):
        def run_step(self, step_name):
            if step_name == 'install_pkg':
                return
            Cheesecake.run_step(self, step_name)

        def __init__(self, sandbox, package_name, logfile):
            self.name = package_name
            self.package_name = package_name
            self.package = package_name
            self.sandbox = sandbox

            self.verbose = False
            self.quiet = True

            self.unpack_dir = sandbox

            self.configure_logging(logfile)
            self.index = CheesecakeIndex()

    def setUp(self):
        self.temp_top_dir = tempfile.mkdtemp()
        self.temp_project_dir = os.path.join(self.temp_top_dir, self.project_name)
        os.mkdir(self.temp_project_dir)

        self._mock_logfile = tempfile.mktemp()

        self.cheesecake = self.CheesecakeMockup(self.temp_top_dir,
                                                self.project_name,
                                                self._mock_logfile)

    def tearDown(self):
        rmtree(self.temp_top_dir)
        os.unlink(self._mock_logfile)

    def create_files(self, files):
        for f in files:
            fd = file(os.path.join(self.temp_top_dir, f), "w")
            fd.write('not_empty')
            fd.close()

    def create_empty_files(self, files):
        create_empty_files_in_directory(files, self.temp_top_dir)

    def prefix_with_package_name(self, files):
        return map(lambda x: os.path.join(self.cheesecake.package_name, x), files)
