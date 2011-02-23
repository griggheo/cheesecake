
import os
import re

from math import ceil

from _helper_cheesecake import FunctionalTest, read_file_contents, DATA_PATH

from cheesecake.util import pad_msg


class TestScore(FunctionalTest):
    def test_required_files(self):
        self._run_cheesecake('-p %s' % os.path.join(DATA_PATH, 'required.tar.gz'))

        self._assert_success()

        stdout = read_file_contents(self.stdout_name)
        # Files in package: INSTALL, Install.html, README and TODO.
        assert '(2 files and 0 required directories found)' in stdout
        # One not documented module with a single function with a docstring.
        assert '(found 1/2=50.00% objects with docstrings)' in stdout
        assert pad_msg('docstrings', 50) in stdout
        assert '(found 0/2=0.00% objects with formatted docstrings)' in stdout

    def test_sum(self):
        installability_regex = r'INSTALLABILITY INDEX \(RELATIVE\) \.\.\.\.\.\.\.\.\s+(\d+)\s+\((\d+) out of a maximum of (\d+) points is (\d+)%\)'
        documentation_regex = r'DOCUMENTATION INDEX \(RELATIVE\) \.\.\.\.\.\.\.\.\.\s+(\d+)\s+\((\d+) out of a maximum of (\d+) points is (\d+)%\)'
        code_kwalitee_regex = r'CODE KWALITEE INDEX \(RELATIVE\) \.\.\.\.\.\.\.\.\.\s+(-*\d+)\s+\((-*\d+) out of a maximum of (\d+) points is (-*\d+)%\)'

        self._run_cheesecake('-p %s' % os.path.join(DATA_PATH, 'required.tar.gz'))

        self._assert_success()

        # Check that scores are added up and scaled properly.
        stdout = read_file_contents(self.stdout_name)

        installability_match = re.search(installability_regex, stdout)
        documentation_match = re.search(documentation_regex, stdout)
        code_kwalitee_match = re.search(code_kwalitee_regex, stdout)

        assert installability_match
        assert documentation_match
        assert code_kwalitee_match

        overall_score = 0
        overall_maximum = 0
        for index in [installability_match, documentation_match, code_kwalitee_match]:
            percent_one, current, maximum, percent_two = index.groups()
            assert percent_one == percent_two
            overall_score += int(current)
            overall_maximum += int(maximum)
            print "Score: %d/%d" % (int(current), int(maximum))

        overall_percent = ceil(overall_score / float(overall_maximum))

        print "Computed overall score: %d" % overall_score
        assert 'OVERALL CHEESECAKE INDEX (ABSOLUTE) .... %3d' % overall_score in stdout
        assert 'OVERALL CHEESECAKE INDEX (RELATIVE) .... %3d  (%d out of a maximum of %d points is %d%%)' % \
               (overall_percent, overall_score, overall_maximum, overall_percent)
