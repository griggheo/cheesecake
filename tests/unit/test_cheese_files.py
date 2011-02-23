
from _mockup_cheesecake import MockupCheesecakeTest


def readlines_from_file(filename):
    fd = open(filename)
    lines = fd.readlines()
    fd.close()
    return lines


def cheesefile_in_log(filename, loglines):
    return "entry found: %s" % filename in loglines


class CheeseFilesTest(MockupCheesecakeTest):
    def _do_it(self, files, create_files, inside_log):
        create_files(self.prefix_with_package_name(files))
        self.cheesecake.walk_pkg()
        self.cheesecake.compute_cheesecake_index()

        loglines = ''.join(readlines_from_file(self._mock_logfile))

        for filename in files:
            print "Checking if %s was counted..." % filename
            assert cheesefile_in_log(filename, loglines) is inside_log

class TestBogusCheeseFiles(CheeseFilesTest):
    def test_bogus_filenames(self):
        bogus_filenames = ['ReAdMe',
                           'install.txt.txt',
                           'setupXpy',
                           'newsXtxt',
                           'todoGARBAGE',
                           'setup.py.txt']
        self._do_it(bogus_filenames, self.create_files, False)

class TestGoodCheeseFiles(CheeseFilesTest):
    def test_good_filenames(self):
        good_filenames = ['Readme', 'INSTALL.txt', 'setup.py', 'news.TXT']
        self._do_it(good_filenames, self.create_files, True)

class TestEmptyCheeseFiles(CheeseFilesTest):
    def test_empty_filenames(self):
        empty_filenames = ['Readme', 'INSTALL', 'setup.py']
        self._do_it(empty_filenames, self.create_empty_files, False)


class TestDoubleFiles(MockupCheesecakeTest):
    def test_double_files(self):
        filenames = ['Readme', 'README.txt']

        self.create_files(self.prefix_with_package_name(filenames))
        self.cheesecake.walk_pkg()
        self.cheesecake.compute_cheesecake_index()

        loglines = ''.join(readlines_from_file(self._mock_logfile))

        # Make sure that README was counted only once.
        assert cheesefile_in_log('Readme', loglines)
        assert not cheesefile_in_log('README.txt', loglines)
