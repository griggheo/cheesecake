#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Compute Cheesecake scores for all packages on PyPI.
#

import datetime
import os
import re
import sys
import time
import urllib2

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(current_dir, '../'))

try:
    import subprocess
except ImportError, ex:
    from cheesecake import subprocess


CHEESECAKE_PATH = os.path.abspath(os.path.join(current_dir,
                                               '../cheesecake_index'))

LOG_PATH = '/tmp/cheesecake_pypi_results'


def read_file_contents(filename):
    fd = file(filename)

    contents = fd.read()
    fd.close()

    return contents

def replace_chars(string):
    replacements = {'%20': '_',
                    '%27': "\\'",
                    '%28': '\\(',
                    '%29': '\\)',
                    '%2A': '\\*',
                    '%3A': ':',
                    '%3F': '\\?',
                    '%C3%B1': 'ñ',
    }

    for From, To in replacements.iteritems():
        string = string.replace(From, To)

    return string

def get_package_names():
    """Get list of all packages on PyPI.

    For each package return (name, version) tuple.
    """
    package_regex = r'<td><a href="/pypi/([^/]+)/([^/]+)">'

    pypi = urllib2.urlopen("http://python.org/pypi?%3Aaction=index")
    html_lines = pypi.readlines()
    pypi.close()

    for line in html_lines:
        m = re.search(package_regex, line)
        if m:
            # To make setuptools download a package, convert all spaces to undescores.
            yield (replace_chars(m.group(1)), replace_chars(m.group(2)))

def score_one_package(package_name, log_template):
    """Score one package leaving information in logs along the way.

    :Logs:
      * .stdout -> Cheesecake stdout
      * .stderr -> Cheesecake stderr
      * .log -> Cheesecake log for given package
    """
    log_file = log_template % 'log'

    stdout_fd = file(log_template % 'stdout', 'w')
    stderr_fd = file(log_template % 'stderr', 'w')

    process = subprocess.Popen('%s -l %s -n %s' % \
                               (CHEESECAKE_PATH, log_file, package_name),
                         stdout=stdout_fd,
                         stderr=stderr_fd,
                         shell=True)

    result = process.wait()

    stdout_fd.close()
    stderr_fd.close()

    if result == 0:
        score_regex = r'OVERALL CHEESECAKE INDEX \(RELATIVE\) \.\.\.\.\s+([\d]+)'
        stdout = read_file_contents(log_template % 'stdout')
        m = re.search(score_regex, stdout)
        if m:
            return int(m.group(1))

    return -1

def time2datetime(t):
    t = time.localtime(t)
    return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday,
                             t.tm_hour, t.tm_min, t.tm_sec)

def time_delta(start, end):
    return str(time2datetime(end) - time2datetime(start))

def score_all_packages():
    packages_failed = []
    packages_scores = []

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    for name, version in get_package_names():
        name_and_version = '%s-%s' % (name, version)
        log_template = os.path.join(LOG_PATH, name_and_version + '.%s')
        start = time.time()
        result = score_one_package('%s==%s' % (name, version), log_template)
        end = time.time()
        if result == -1:
            packages_failed.append(name_and_version)
        else:
            packages_scores.append((name_and_version, result, time_delta(start, end)))

    print "=== Packages that Cheesecake failed to score ==="
    for failed in packages_failed:
        print failed

    print
    print "=== All packages scores ==="
    # Sorty by score.
    packages_scores.sort(lambda x,y: cmp(x[1], y[1]))

    for name, score, timing in packages_scores:
        print "%s SCORE:%s (in %s time)" % (name, score, timing)

    print
    print "=== Summary ==="
    print "Checked %d packages in overall." % (len(packages_scores) + len(packages_failed))
    print "Failed for %d." % len(packages_failed)
    print "%d packages got more than 50%% Cheesecake score." % len(filter(lambda x: x[1] > 50, packages_scores))


if __name__ == '__main__':
    score_all_packages()

