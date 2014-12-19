import os
import shutil
import tempfile

from math import ceil

import _path_cheesecake

from cheesecake.cheesecake_index import Cheesecake
from cheesecake.cheesecake_index import IndexUnitTested
from cheesecake.util import rmtree
from cheesecake import logger

from _helper_cheesecake import create_empty_files_in_directory


def dump_str_to_file(string, filename):
    fd = file(filename, 'w')
    fd.write(string)
    fd.close()


main_contents = """
class SomeClass(object):
    '''This is a docstring with doctests.

    >>> print("Hello")
    Hello
    '''
    def method(self):
        'No doctest here.'
        pass

def function_without_docstring(x):
    return x**x
"""

test_contents = """
class TestSomeModule:
    def setUp(self):
        pass
    def test_this(self):
        pass
    def test_that(self):
        pass
"""

unittest_test_contents = """
class TestThisAndThat(unittest.TestCase):
    def test_this(self):
        pass
"""

class TestIndexUnitTested(object):
    def setUp(self):
        self.sandbox_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.sandbox_dir):
            rmtree(self.sandbox_dir)

    def test_doctest(self):
        "Test unit_tested index with package that uses doctest."
        def setup(project_dir):
            main_filename = os.path.join(project_dir, 'main.py')
            dump_str_to_file(main_contents, main_filename)

        def asserts(cheesecake):
            assert cheesecake.functions == ['main.function_without_docstring']
            assert cheesecake.classes == ['main.SomeClass']

        self._run_it(setup, asserts)

    def _run_it(self, setup=None, asserts=None):
        package_name = 'index_test'

        project_dir = os.path.join(self.sandbox_dir, package_name)
        os.mkdir(project_dir)

        if setup:
            setup(project_dir)

        logger.setconsumer('console', logger.STDOUT)
        console_log = logger.MultipleProducer('cheesecake console')

        # Aliasing package_name because of Python optimizations.
        #     ("package_name = package_name" will simply not work)
        pkg_name = package_name

        class CheesecakeMockup(Cheesecake):
            def __init__(self):
                pass
            sandbox = self.sandbox_dir
            package_name = pkg_name
            log = console_log

        cheesecake = CheesecakeMockup()
        cheesecake.walk_pkg()

        if asserts:
            asserts(cheesecake)

        index = IndexUnitTested()
        index.compute_with(cheesecake)

        # Unit tests presence should be discovered and package should get
        # maximum score.
        print("Index: %d/%d -- %s" %
              (index.value, index.max_value, index.details))
        assert index.value == index.max_value

    def test_special_filenames_1(self):
        "Test unit_tested index with package that uses test_* filenames."
        def setup(project_dir):
            files = ['some_module.py', 'README', 'test_some_module.py']
            create_empty_files_in_directory(files, project_dir)

        self._run_it(setup)

    def test_special_filenames_2(self):
        "Test unit_tested index with package that uses *_test filenames."
        def setup(project_dir):
            files = ['some_module.py', 'README', 'some_module_test.py']
            create_empty_files_in_directory(files, project_dir)

        self._run_it(setup)

    def test_special_methods(self):
        "Test unit_tested index with package that uses setUp/tearDown methods."
        def setup(project_dir):
            test_filename = os.path.join(project_dir, 'do_checks.py')
            dump_str_to_file(test_contents, test_filename)

        self._run_it(setup)

    def test_unittest_classes(self):
        "Test unit_tested index with package that uses unittest library."
        def setup(project_dir):
            test_filename = os.path.join(project_dir, 'do_checks.py')
            dump_str_to_file(unittest_test_contents, test_filename)

        self._run_it(setup)
