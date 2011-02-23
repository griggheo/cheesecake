~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Cheesecake: How tasty is your code?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. contents:: **Table of Contents**

Summary
-------

The idea of the Cheesecake project is to rank Python packages based on various 
empirical "kwalitee" factors, such as:

 * whether the package can be downloaded from PyPI given its name
 * whether the package can be unpacked
 * whether the package can be installed into an alternate directory
 * existence of certain files such as README, INSTALL, LICENSE, setup.py etc.
 * percentage of modules/functions/classes/methods with docstrings
 * pylint score
 * ... and many others

Currently, the Cheesecake index is computed for invidual packages obtained 
through a variety of methods (detailed below). One of the goals of the 
Cheesecake project is to automatically compute the Cheesecake index for 
all packages uploaded to the PyPI Cheese Shop (possibly at upload time) and 
to maintain a collection of Web pages with statistics related to the 
various indexes of the packages.

Cheesecake currently computes 3 types of indexes:

 * installability index
 * documentation index
 * code kwalitee index

The algorithms for computing each index type are detailed below.

Why Cheesecake?
---------------

The concept of "kwalitee" originated in the Perl community. Here's a relevant
quote:

  * It looks like quality, it sounds like quality, but it's not quite quality.*

Kwalitee is an empiric measure of how good a specific body of code is. It 
defines quality indicators and measures the code along them. It is currently 
used by the `CPANTS Testing Service <http://cpants.dev.zsi.at/index.html>`_
to evaluate the 'goodness' of CPAN packages.

Since the Python package repository (aka `PyPI <http://www.python.org/pypi>`_) 
is hosted at the Cheese Shop,
it stands to reason that the quality indicator of a PyPI package should be 
called the Cheesecake index!

Usage examples
--------------

To compute the Cheesecake index for a given project, run the cheesecake_index
script from the command line and indicate either:

 * the package short name (e.g. twill) or
 * the package URL (e.g. http://darcs.idyll.org/~t/projects/twill-0.7.4.tar.gz) or
 * the package path on the file system (e.g. /tmp/twill-latest.tar.gz)

In all cases, the cheesecake script will attempt to download the package
if necessary, then to unpack it in a sandbox directory (/tmp/cheesecake_sandbox 
by default). If either of these operations fails, the Cheesecake index for 
the package will be 0. If the package can be successfully unpacked, the 
cheesecake script will compute the values for a variety of indexes detailed
in the algorithm given at the end of this file.

If the package can be successfully downloaded and unpacked, a log file is
created in the system /tmp directory and named <package>.log (e.g. the log file 
for twill-0.7.4.tar.gz is /tmp/twill-0.7.4.tar.gz.log).
The log file is automatically deleted after the Cheesecake index is
computed, except for situations when errors have occured.

Command-line examples:

 1. Compute the Cheesecake index for the Durus package by using setuptools
    utilities to download the package from PyPI::

      python cheesecake_index --name=Durus

 2. Compute the Cheesecake index for the Durus package by indicating its URL::

      python cheesecake_index --url=http://www.mems-exchange.org/software/durus/Durus-3.1.tar.gz

 3. Compute the Cheesecake index for the twill package by indicating its path 
    on the local file system::

      python cheesecake_index --path=/tmp/twill-latest.tar.gz

 4. To increase the verbosity of the output, use the -v or --verbose option. 
    For more options, run cheesecake_index with -h or --help.

Requirements
------------

* `pylint <http://www.logilab.org/projects/pylint>`_ is required for
  part of the code kwalitee index computation 
* `setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_ is
  required for the installability index computation

Obtaining the source code
-------------------------

You can get the source code via svn::

  svn co http://svn.pycheesecake.org/trunk cheesecake

*Note*: make sure you indicate the target directory when you do the svn checkout,
otherwise the cheesecake package files will be checked out directly in your
current directory.

You may want to modify your subversion client configuration to automatically
expand tags, like $Id$, $Author$ etc. To do so add following two lines to your
``/.subversion/config``::

  enable-auto-props = yes

in [miscellany] section, and::

  *.py = svn:eol-style=native;svn:keywords=Author Date Id Revision

in [auto-props] section.

Documentation
-------------

The most recent code documentation should be always available
at http://agilistas.org/cheesecake/mk/docs/. You can also generate
this documentation directly from the Cheesecake sources. Run this command
from the main source directory::

  sh support/generate_docs.sh .

:Note: Generating documentation requires `epydoc <http://epydoc.sourceforge.net/>`_
       tool installed.

Unit tests
----------

We use `nose <http://somethingaboutorange.com/mrl/projects/nose/>`_ for automatic
testing of our project, so if you want to test Cheesecake on your machine, please
install that first. Running the standard set of Cheesecake unit test is as easy as::

  python setup.py test

This command is equivalent to::

  nosetests --verbose --with-doctest --doctest-tests --include unit --exe

We also have a set of functional tests, which can be run by issuing this command::

  nosetests --verbose --include functional

Functional tests can take a bit longer to complete, as they test cheesecake_index
script as a whole (as opposed to testing modules and classes separately).

If you happen to find any of our tests failing, please don't hesitate to contact
us, either via
`cheesecake-devel mailing list <http://lists2.idyll.org/listinfo/cheesecake-dev>`_
or via `Cheesecake Trac <http://pycheesecake.org/>`_.

Buildbot
--------

A buildbot is happily running svn updates and unit tests. Check it out
`here <http://agilistas.org:8888/>`_.

Mailing lists
-------------

* Developer mailing list: http://lists2.idyll.org/listinfo/cheesecake-dev
* User mailing list: http://lists2.idyll.org/listinfo/cheesecake-users

License
-------

Cheesecake is licensed under the Python Software Foundation license, 
the same license that governs Python itself. The text of the license is
available in the ``LICENSE`` file in the source code distribution and
can also be downloaded from 
http://www.opensource.org/licenses/PythonSoftFoundation.php.

Authors contact info
--------------------

Grig Gheorghiu

:Email: <grig at gheorghiu dot net>
:Web site: http://agiletesting.blogspot.com

Michal Kwiatkowski

:Email: <ruby at joker.linuxstuff.pl>
:Web site: http://joker.linuxstuff.pl

Note: clipart for the cheesecake slice logo used with permission from
Kazumi Hatasa, Director, the Japanese School at Middlebury College,
Purdue University.

Algorithm for computing the Cheesecake index
--------------------------------------------

The overall Cheesecake score is the sum of values of 3 main indexes
(installability, documentation and code kwalitee). The values of these
indexes rely on values of their subindexes and so on. The whole index tree
and corresponding values for each leaf are presented below:

* Installability

  * package is listed on and can be downloaded from PyPI: 50
  * package can be downloaded from given URL: 25
  * package can be unpacked without problems: 25
  * unpacked package directory is the same as package name: 15
  * package has setup.py: 25
  * package can be installed to given directory via "setup.py install": 50
  * package contain generated files, like .pyc: -20

* Documentation

  * package contain files listed below

    * README: 30
    * LICENCE/COPYING: 30 [#oneof]_
    * ANNOUNCE/CHANGELOG: 20 [#oneof]_
    * INSTALL: 20
    * AUTHORS: 10
    * FAQ: 10
    * NEWS: 10
    * THANKS: 10
    * TODO: 10

  * package contain directories listed below

    * doc/docs: 30 [#oneof]_
    * test/tests: 30 [#oneof]_
    * demo/example/examples: 10 [#oneof]_

  * code is documented by docstrings: 100 [#docstrings]_
  * docstrings have proper formatting (like epytext or reST): 30 [#formatted]_

* Code Kwalitee

  * package has high pylint score: 50
  * package has unit tests: 30
  * (optional) package doesn't follow PEP8 conventions [#PEP8]_: -2 for each error type and -1 for each warning type

The final score depends on how well the package scores for all indexes
listed above. The score is presented in absolute range (number of points)
and relative (percent of points obtained compared to maximum possible points).

.. [#oneof] It is enough for a package to contain only one of listed files.
.. [#docstrings] Number of points is proportional to percent of documentable objects
   (module, class or function) that have docstrings. For example, if
   you have 50 documentable objects and 32 of them have docstrings
   your code will get 64 points (because 64% of objects are documented).
.. [#formatted] Number of points depends on number of docstrings that are found
   to contain one of known markup. Currently ReST, epytext and javadoc are
   recognized. We give 10 points for 25% of formatted docstrings, 20 points
   for 50% and 30 points for 75%.
.. [#PEP8] PEP8 defines a good coding style for Python, see
   `PEP8 document <http://www.python.org/dev/peps/pep-0008/>`_ for details.

Sample output
-------------

::

    $ python cheesecake_index -n nose --with-pep8
    py_pi_download .........................  50  (downloaded package nose-0.9.1.tar.gz following 1 link from http://somethingaboutorange.com/mrl/projects/nose/nose-0.9.1.tar.gz)
    unpack .................................  25  (package unpacked successfully)
    unpack_dir .............................  15  (unpack directory is nose-0.9.1 as expected)
    setup.py ...............................  25  (setup.py found)
    install ................................  50  (package installed in /tmp/cheesecakeOzL_mb/tmp_install_nose-0.9.1)
    generated_files ........................   0  (0 .pyc and 0 .pyo files found)
    ---------------------------------------------
    INSTALLABILITY INDEX (ABSOLUTE) ........ 165
    INSTALLABILITY INDEX (RELATIVE) ........ 100  (165 out of a maximum of 165 points is 100%)

    required_files ......................... 110  (4 files and 2 required directories found)
    docstrings .............................  43  (found 139/329=42.25% objects with docstrings)
    formatted_docstrings ...................   0  (found 53/329=16.11% objects with formatted docstrings)
    ---------------------------------------------
    DOCUMENTATION INDEX (ABSOLUTE) ......... 153
    DOCUMENTATION INDEX (RELATIVE) .........  44  (153 out of a maximum of 350 points is 44%)

    unit_tested ............................  30  (has unit tests)
    pylint .................................  37  (pylint score was 7.29 out of 10)
    pep8 ................................... -16  (pep8.py check: 7 error types, 2 warning types)
    ---------------------------------------------
    CODE KWALITEE INDEX (ABSOLUTE) .........  51
    CODE KWALITEE INDEX (RELATIVE) .........  64  (51 out of a maximum of 80 points is 64%)


    =============================================
    OVERALL CHEESECAKE INDEX (ABSOLUTE) .... 369
    OVERALL CHEESECAKE INDEX (RELATIVE) ....  62  (369 out of a maximum of 595 points is 62%)

Case study: Cleaning up PyBlosxom
---------------------------------

Many thanks to Will Guaraldi for writing
`this article <http://pycheesecake.org/wiki/CleaningUpPyBlosxom>`_ about his
experiences in using Cheesecake to clean up and improve the structure of his
PyBlosxom package.
    
Future plans
------------
Cheesecake is under very active development. The immediate goal is to add the unit test 
index measurement, followed by other metrics inspired from the 
`kwalitee indicators <http://cpants.dev.zsi.at/kwalitee.html>`_. 
Please edit the `IndexMeasurementIdeas <http://pycheesecake.org/wiki/IndexMeasurementIdeas>`_
Wiki page to add things that you would like to see covered 
by the Cheesecake metrics.

.. footer:: Last modified: 31 Jan 2007 by `Michal Kwiatkowski <http://joker.linuxstuff.pl>`_.
