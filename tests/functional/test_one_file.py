import os

from _helper_cheesecake import FunctionalTest, read_file_contents, DATA_PATH


class TestOneFile(FunctionalTest):
    def test_one_file(self):
        "Make sure that archives with one file are handled properly."
        self._run_cheesecake('-p %s' % (os.path.join(DATA_PATH, 'module1.tar.gz')))

        self._assert_success()

