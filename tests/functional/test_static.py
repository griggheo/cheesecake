
import os
import tempfile

from _helper_cheesecake import FunctionalTest, DATA_PATH


special_file_name = os.path.join(tempfile.gettempdir(), 'cheesecake_special')


class TestStatic(FunctionalTest):
    def test_static(self):
        self._run_cheesecake('-p %s --static' % os.path.join(DATA_PATH, 'static.tar.gz'))

        self._assert_success()
        assert not os.path.exists(special_file_name)

    def tearDown(self):
        self._cleanup()

        if os.path.exists(special_file_name):
            os.unlink(special_file_name)
