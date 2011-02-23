#! /usr/bin/env python
import sys
import os

from setuptools import setup
from pkg_resources import require
from cheesecake import __version__ as VERSION

# Instruct nose to use doctests.
os.environ['NOSE_WITH_DOCTEST'] = 'True'
os.environ['NOSE_DOCTEST_TESTS'] = 'True'
os.environ['NOSE_INCLUDE'] = 'unit'
os.environ['NOSE_INCLUDE_EXE'] = 'True'

setup(
        name = 'Cheesecake',
        version = VERSION,

        # metadata for upload to PyPI
        author = "Grig Gheorghiu and Michal Kwiatkowski",
        author_email = "grig@gheorghiu.net and ruby@joker.linuxstuff.pl",
        description = 'Computes "goodness" index for Python packages based on various empirical "kwalitee" factors',
        license = "PSF",
        keywords = "cheesecake quality index kwalitee cheeseshop pypi",
        url = "http://pycheesecake.org/",

        packages = ['cheesecake',
                    ],
        scripts = ['cheesecake_index',
                    ],
        entry_points = {
            'console_scripts': [
                'cheesecake_index = cheesecake.cheesecake_index:main',
            ]
        },
        test_suite = 'nose.collector',
        tests_require = ['nose']
)
