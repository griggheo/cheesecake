import os
import shutil
import tempfile

from math import ceil

import _path_cheesecake
from _helper_cheesecake import dump_str_to_file

from cheesecake.cheesecake_index import IndexUnitTests
from cheesecake import logger
from cheesecake.util import rmtree


test_contents = """
import some_module
import different_module

class TestSomeFunction:
    def test_some_function(self):
        value = some_module.some_function(4, 2)
        assert value is True

    def test_a_method(self):
        self.object = some_module.SomeClass()

    def test_different_module(self):
        self.object = different_module.NotTestedClass()
        different_module.some_module.some_function()
"""

class TestUnitTestsIndex(object):
    def setUp(self):
        self.project_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.project_dir):
            rmtree(self.project_dir)

    def test_unit_tests_index(self):
        test_dir = os.path.join(self.project_dir, 'test')
        os.mkdir(test_dir)

        test_filename = os.path.join(test_dir, 'test_some_function.py')
        dump_str_to_file(test_contents, test_filename)

        logger.setconsumer('console', logger.STDOUT)
        console_log = logger.MultipleProducer('cheesecake console')

        class CheesecakeMockup(object):
            files_list = [test_filename]
            functions = ["some_module.some_function",
                         "some_module.other_function"]
            classes = ["some_module.SomeClass",
                       "some_module.NotTestedClass"]
            package_dir = self.project_dir
            log = console_log

        index = IndexUnitTests()

        index.compute_with(CheesecakeMockup())

        print("Index: %d/%d -- %s" %
              (index.value, index.max_value, index.details))
        assert index.value == int(ceil(index.max_value * 2.0/4.0))
