
import _path_cheesecake
from cheesecake.cheesecake_index import get_files_of_type

from _mockup_cheesecake import MockupCheesecakeTest
from _helper_cheesecake import set


class TestNoTestFiles(MockupCheesecakeTest):
    def test_discover_no_test_files(self):
        py_files = ['main.py', 'module.py']
        self.create_files(self.prefix_with_package_name(py_files))
        self.cheesecake.walk_pkg()
        self.cheesecake.compute_cheesecake_index()

        def get_list(type):
            return get_files_of_type(self.cheesecake.files_list, type)

        assert set(get_list('module')) == set(py_files)
        assert get_list('pyc') == []
        assert get_list('pyo') == []
        assert get_list('test') == []


class TestPycPyoFiles(MockupCheesecakeTest):
    def test_some_pyc_and_pyo_files(self):
        py_files = ['main.py']
        pyc_files = ['main.pyc', 'missing.pyc']
        pyo_files = ['main.pyo', 'optimised.pyo']

        self.create_files(self.prefix_with_package_name(py_files + pyc_files + pyo_files))
        self.cheesecake.walk_pkg()
        self.cheesecake.compute_cheesecake_index()

        def get_list(type):
            return get_files_of_type(self.cheesecake.files_list, type)

        assert set(get_list('module')) == set(py_files)
        assert set(get_list('pyc')) == set(pyc_files)
        assert set(get_list('pyo')) == set(pyo_files)
        assert get_list('test') == []
