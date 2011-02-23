import os
import tempfile

import _path_cheesecake
from _helper_cheesecake import VALID_URLS
from _helper_cheesecake import mocked_urlretrieve

import cheesecake.cheesecake_index as cheesecake_index
from cheesecake.cheesecake_index import Cheesecake, CheesecakeError, pad_msg, IndexUrlDownload
        
default_temp_directory = os.path.join(tempfile.gettempdir(), 'cheesecake_sandbox')


class TestIndexInstallability(object):
    def setUp(self):
        self.cheesecake = None
        cheesecake_index.urlretrieve = mocked_urlretrieve

    def _run_it(self, test_fun):
        logfile = tempfile.mktemp()

        try:
            test_fun(logfile)
        finally:
            if self.cheesecake:
                self.cheesecake.cleanup()

            if os.path.exists(logfile):
                os.unlink(logfile)

    def test_index_url_download_valid_url(self):
        urls = VALID_URLS

        for url in urls:
            def test_fun(logfile):
                self.cheesecake = Cheesecake(url=url, logfile=logfile)

                index = self.cheesecake.index["INSTALLABILITY"]["IndexUrlDownload"]
                index.compute_with(self.cheesecake)

                assert index.name == "IndexUrlDownload"
                assert index.value == IndexUrlDownload.max_value
                assert index.details == "downloaded package " + \
                       self.cheesecake.package + " from URL " + \
                       self.cheesecake.url

            self._run_it(test_fun)

    def test_index_url_download_invalid_url(self):
        def test_fun(logfile):
            try:
                self.cheesecake = Cheesecake(url="invalid_url",
                                             sandbox=default_temp_directory, logfile=logfile)
                assert False, "Should throw a CheesecakeError."
            except CheesecakeError, e:
                msg = "Error: Got '404 Not Found' error while trying to download package ... exiting"
                msg += "\nDetailed info available in log file %s" % logfile
                assert str(e) == msg

        self._run_it(test_fun)

    def test_index_url_download_connection_refused(self):
        def test_fun(logfile):
            try:
                self.cheesecake = Cheesecake(url='connection_refused',
                                             sandbox=default_temp_directory, logfile=logfile)
                assert False, "Should throw a CheesecakeError."
            except CheesecakeError, e:
                print str(e)
                msg = "Error: [Errno socket error] (111, 'Connection refused')\n"
                msg += "Detailed info available in log file %s" % logfile
                assert str(e) == msg

        self._run_it(test_fun)
