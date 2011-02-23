import os
from math import ceil

import _path_cheesecake
from _helper_cheesecake import DATA_PATH
from cheesecake.cheesecake_index import Cheesecake, CodeParser


class TestIndexDocstrings(object):
    def setUp(self):
        self.cheesecake = Cheesecake(path=os.path.join(DATA_PATH, "package2.tar.gz"))

        modules = 5
        classes = 2
        functions = 4
        methods = 3

        self.documentable_objects = modules + classes + functions + methods
        self.docstring_count = 7

        self.index_float = float(self.docstring_count) / self.documentable_objects
        self.index_int = int(ceil(self.index_float*100))

    def tearDown(self):
        self.cheesecake.cleanup()

    def test_index_docstrings(self):
        index = self.cheesecake.index["DOCUMENTATION"]["IndexDocstrings"]
        index.compute_with(self.cheesecake)

        assert index.name == "IndexDocstrings"
        assert index.value == self.index_int
        assert index.details == "found %d/%d=%.2f%% objects with docstrings" %\
                            (self.docstring_count, self.documentable_objects, self.index_float*100)
