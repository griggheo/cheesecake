#!/usr/bin/env python
"""Cheesecake: How tasty is your code?

The idea of the Cheesecake project is to rank Python packages based on various
empirical "kwalitee" factors, such as:

 * whether the package can be downloaded from PyPI given its name
 * whether the package can be unpacked
 * whether the package can be installed into an alternate directory
 * existence of certain files such as README, INSTALL, LICENSE, setup.py etc.
 * percentage of modules/functions/classes/methods with docstrings
 * ... and many others
"""

import os
import re
import shutil
import sys
import tempfile

from optparse import OptionParser
from urllib import urlretrieve
from urlparse import urlparse
from math import ceil

import logger

from util import pad_with_dots, pad_left_spaces, pad_right_spaces, pad_msg, pad_line
from util import run_cmd, command_successful
from util import unzip_package, untar_package, unegg_package
from util import mkdirs
from util import StdoutRedirector
from util import time_function
from util import rmtree
from codeparser import CodeParser
from __init__ import __version__ as VERSION
import pep8

import warnings
warnings.filterwarnings("ignore", message="the sets module is deprecated")

__docformat__ = 'reStructuredText en'
__revision__ = '$Revision: 192 $'[11:-1].strip()


################################################################################
## Helpers.
################################################################################

if 'sorted' not in dir(__builtins__):
    def sorted(L):
        new_list = L[:]
        new_list.sort()
        return new_list

if 'set' not in dir(__builtins__):
    from sets import Set as set

def isiterable(obj):
    """Check whether object is iterable.

    >>> isiterable([1,2,3])
    True
    >>> isiterable("string")
    True
    >>> isiterable(object)
    False
    """
    return hasattr(obj, '__iter__') or isinstance(obj, basestring)

def has_extension(filename, ext):
    """Check if filename has given extension.

    >>> has_extension("foobar.py", ".py")
    True
    >>> has_extension("foo.bar.py", ".py")
    True
    >>> has_extension("foobar.pyc", ".py")
    False

    This function is case insensitive.
        >>> has_extension("FOOBAR.PY", ".py")
        True
    """
    return os.path.splitext(filename.lower())[1] == ext.lower()

def discover_file_type(filename):
    """Discover type of a file according to its name and its parent directory.

    Currently supported file types:
        * pyc
        * pyo
        * module: .py files of an application
        * demo: .py files for documentation/demonstration purposes
        * test: .py files used for testing
        * special: .py file for special purposes

    :Note: This function only checks file's name, and doesn't touch the
           filesystem. If you have to, check if file exists by yourself.

    >>> discover_file_type('module.py')
    'module'
    >>> discover_file_type('./setup.py')
    'special'
    >>> discover_file_type('some/directory/junk.pyc')
    'pyc'
    >>> discover_file_type('examples/readme.txt')
    >>> discover_file_type('examples/runthis.py')
    'demo'
    >>> discover_file_type('optimized.pyo')
    'pyo'

    >>> test_files = ['ut/test_this_and_that.py',
    ...               'another_test.py',
    ...               'TEST_MY_MODULE.PY']
    >>> for filename in test_files:
    ...     assert discover_file_type(filename) == 'test', filename

    >>> discover_file_type('this_is_not_a_test_really.py')
    'module'
    """
    dirs = filename.split(os.path.sep)
    dirs, filename = dirs[:-1], dirs[-1]

    if filename in ["setup.py", "ez_setup.py", "__pkginfo__.py"]:
        return 'special'

    if has_extension(filename, ".pyc"):
        return 'pyc'
    if has_extension(filename, ".pyo"):
        return 'pyo'
    if has_extension(filename, ".py"):
        for dir in dirs:
            if dir in ['test', 'tests']:
                return 'test'
            elif dir in ['doc', 'docs', 'demo', 'example', 'examples']:
                return 'demo'

        # Most test frameworks look for files starting with "test_".
        # py.test also looks at files with trailing "_test".
        if filename.lower().startswith('test_') or \
               os.path.splitext(filename)[0].lower().endswith('_test'):
            return 'test'

        return 'module'

def get_files_of_type(file_list, file_type):
    """Return files from `file_list` that match given `file_type`.

    >>> file_list = ['test/test_foo.py', 'setup.py', 'README', 'test/test_bar.py']
    >>> get_files_of_type(file_list, 'test')
    ['test/test_foo.py', 'test/test_bar.py']
    """
    return filter(lambda x: discover_file_type(x) == file_type, file_list)

def get_package_name_from_path(path):
    """Get package name as file portion of path.

    >>> get_package_name_from_path('/some/random/path/package.tar.gz')
    'package.tar.gz'
    >>> get_package_name_from_path('/path/underscored_name.zip')
    'underscored_name.zip'
    >>> get_package_name_from_path('/path/unknown.extension.txt')
    'unknown.extension.txt'
    """
    dir, filename = os.path.split(path)
    return filename

def get_package_name_from_url(url):
    """Use ``urlparse`` to obtain package name from URL.

    >>> get_package_name_from_url('http://www.example.com/file.tar.bz2')
    'file.tar.bz2'
    >>> get_package_name_from_url('https://www.example.com/some/dir/file.txt')
    'file.txt'
    """
    (scheme,location,path,param,query,fragment_id) = urlparse(url)
    return get_package_name_from_path(path)

def get_package_name_and_type(package, known_extensions):
    """Return package name and type.

    Package type must exists in known_extensions list. Otherwise None is
    returned.

    >>> extensions = ['tar.gz', 'zip']
    >>> get_package_name_and_type('underscored_name.zip', extensions)
    ('underscored_name', 'zip')
    >>> get_package_name_and_type('unknown.extension.txt', extensions)
    """
    for package_type in known_extensions:
        if package.endswith('.'+package_type):
            # Package name is name of package without file extension (ex. twill-7.3).
            return package[:package.rfind('.'+package_type)], package_type

def get_method_arguments(method):
    """Return tuple of arguments for given method, excluding self.

    >>> class Class:
    ...     def method(s, arg1, arg2, other_arg):
    ...         pass
    >>> get_method_arguments(Class.method)
    ('arg1', 'arg2', 'other_arg')
    """
    return method.func_code.co_varnames[1:method.func_code.co_argcount]

def get_attributes(obj, names):
    """Return attributes dictionary with keys from `names`.

    Object is queried for each attribute name, if it doesn't have this
    attribute, default value None will be returned.

    >>> class Class:
    ...     pass
    >>> obj = Class()
    >>> obj.attr = True
    >>> obj.value = 13
    >>> obj.string = "Hello"

    >>> d = get_attributes(obj, ['attr', 'string', 'other'])
    >>> d == {'attr': True, 'string': "Hello", 'other': None}
    True
    """
    attrs = {}

    for name in names:
        attrs[name] = getattr(obj, name, None)

    return attrs

def camel2underscore(name):
    """Convert name from CamelCase to underscore_name.

    >>> camel2underscore('CamelCase')
    'camel_case'
    >>> camel2underscore('already_underscore_name')
    'already_underscore_name'
    >>> camel2underscore('BigHTMLClass')
    'big_html_class'
    >>> camel2underscore('')
    ''
    """
    if name and name[0].upper:
        name = name[0].lower() + name[1:]

    def capitalize(match):
        string = match.group(1).lower().capitalize()
        return string[:-1] + string[-1].upper()

    def underscore(match):
        return '_' + match.group(1).lower()

    name = re.sub(r'([A-Z]+)', capitalize, name)
    return re.sub(r'([A-Z])', underscore, name)

def index_class_to_name(clsname):
    """Covert index class name to index name.

    >>> index_class_to_name("IndexDownload")
    'download'
    >>> index_class_to_name("IndexUnitTests")
    'unit_tests'
    >>> index_class_to_name("IndexPyPIDownload")
    'py_pi_download'
    """
    return camel2underscore(clsname.replace('Index', '', 1))

def is_empty(path):
    """Returns True if file or directory pointed by `path` is empty.
    """
    if os.path.isfile(path) and os.path.getsize(path) == 0:
        return True
    if os.path.isdir(path) and os.listdir(path) == []:
        return True

    return False

def strip_dir_part(path, root):
    """Strip `root` part from `path`.

    >>> strip_dir_part('/home/ruby/file', '/home')
    'ruby/file'
    >>> strip_dir_part('/home/ruby/file', '/home/')
    'ruby/file'
    >>> strip_dir_part('/home/ruby/', '/home')
    'ruby/'
    >>> strip_dir_part('/home/ruby/', '/home/')
    'ruby/'
    """
    path = path.replace(root, '', 1)

    if path.startswith(os.path.sep):
        path = path[1:]

    return path

def get_files_dirs_list(root):
    """Return list of all files and directories below `root`.

    Root directory is excluded from files/directories paths.
    """
    files = []
    directories = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = strip_dir_part(dirpath, root)
        files.extend(map(lambda x: os.path.join(dirpath, x), filenames))
        directories.extend(map(lambda x: os.path.join(dirpath, x), dirnames))

    return files, directories

def length(L):
    """Overall length of all strings in list.

    >>> length(['a', 'bc', 'd', '', 'efg'])
    7
    """
    return sum(map(lambda x: len(x), L))

def generate_arguments(arguments, max_length):
    """Pass list of strings in chunks of size not greater than max_length.

    >>> for x in generate_arguments(['abc', 'def'], 4):
    ...     print x
    ['abc']
    ['def']

    >>> for x in generate_arguments(['a', 'bc', 'd', 'e', 'f'], 2):
    ...     print x
    ['a']
    ['bc']
    ['d', 'e']
    ['f']

    If a single argument is larger than max_length, ValueError is raised.
        >>> L = []
        >>> for x in generate_arguments(['abc', 'de', 'fghijk', 'l'], 4):
        ...     L.append(x)
        Traceback (most recent call last):
          ...
        ValueError: Argument 'fghijk' larger than 4.
        >>> L
        [['abc'], ['de']]
    """
    L = []
    i = 0

    # We have to look ahead, so C-style loop here.
    while arguments:
        if L == [] and len(arguments[i]) > max_length:
            raise ValueError("Argument '%s' larger than %d." % (arguments[i], max_length))

        L.append(arguments[i])

        # End of arguments: yield then terminate.
        if i == len(arguments) - 1:
            yield L
            break

        # Adding next argument would exceed max_length, so yield now.
        if length(L) + len(arguments[i+1]) > max_length:
            yield L
            L = []

        i += 1

################################################################################
## Main index class.
################################################################################

class NameSetter(type):
    def __init__(cls, name, bases, dict):
        if 'name' not in dict:
            setattr(cls, 'name', name)

        if 'compute_with' in dict:
            orig_compute_with = cls.compute_with

            def _timed_compute_with(self, cheesecake):
                (ret, self.time_taken) = time_function(lambda: orig_compute_with(self, cheesecake))
                self.cheesecake.log.debug("Index %s computed in %.2f seconds." % (self.name, self.time_taken))
                return ret

            setattr(cls, 'compute_with', _timed_compute_with)

    def __repr__(cls):
        return '<Index class: %s>' % cls.name

def make_indices_dict(indices):
    indices_dict = {}
    for index in indices:
        indices_dict[index.name] = index
    return indices_dict

class Index(object):
    """Class describing one index.

    Use it as a container index or subclass to create custom indices.

    During class initialization, special attribute `name` is magically
    set based on class name. See `NameSetter` definitions for details.
    """
    __metaclass__ = NameSetter

    subindices = None

    name = "unnamed"
    value = -1
    details = ""
    info = ""

    def __init__(self, *indices):
        # When indices are given explicitly they override the default.
        if indices:
            self.subindices = []
            self._indices_dict = {}
            for index in indices:
                self.add_subindex(index)
        else:
            if self.subindices:
                new_subindices = []
                for index in self.subindices:
                    # index must be a class subclassing from Index.
                    assert isinstance(index, type)
                    assert issubclass(index, Index)
                    new_subindices.append(index())
                self.subindices = new_subindices
            else:
                self.subindices = []
            # Create dictionary for fast reference.
            self._indices_dict = make_indices_dict(self.subindices)

        self._compute_arguments = get_method_arguments(self.compute)

    def _iter_indices(self):
        """Iterate over each subindex and yield their values.
        """
        for index in self.subindices[:]:
            try:
                # Pass Cheesecake instance to a subindex.
                yield index.compute_with(self.cheesecake)
                # Print index info after computing.
                if not self.cheesecake.quiet:
                    index.print_info()
            except:
                # When exception is thrown, silence it
                #   and remove this subindex from the list.
                self.subindices.remove(index)

    def compute_with(self, cheesecake):
        """Take given Cheesecake instance and compute index value.
        """
        self.cheesecake = cheesecake
        return self.compute(**get_attributes(cheesecake, self._compute_arguments))

    def compute(self):
        """Compute index value and return it.

        By default this method computes sum of all subindices. Override this
        method when subclassing for different behaviour.

        Parameters to this function are dynamically prepared with use of
        `get_attributes` function.

        :Warning: Don't use \*args and \*\*kwds arguments for this method.
        """
        self.value = sum(self._iter_indices())
        return self.value

    def decide(self, cheesecake, when):
        """Decide if this index should be computed.

        If index has children, it will automatically remove all for which
        decide() return false.
        """
        if self.subindices:
            # Iterate over copy, as we may remove some elements.
            for index in self.subindices[:]:
                if not getattr(index, 'decide_' + when)(cheesecake):
                    self.remove_subindex(index.name)
            return self.subindices
        return True

    def decide_before_download(self, cheesecake):
        return self.decide(cheesecake, 'before_download')

    def decide_after_download(self, cheesecake):
        return self.decide(cheesecake, 'after_download')

    def add_info(self, info_line):
        """Add information about index computation process, which will
        be visible with --verbose flag.
        """
        self.info += "[%s] %s\n" % (index_class_to_name(self.name), info_line)

    def _get_max_value(self):
        if self.subindices:
            return sum(map(lambda index: index.max_value,
                           self.subindices))
        return 0

    max_value = property(_get_max_value)

    def _get_requirements(self):
        if self.subindices:
            return list(self._compute_arguments) + \
                   reduce(lambda x,y: x + y.requirements, self.subindices, [])
        return list(self._compute_arguments)

    requirements = property(_get_requirements)

    def add_subindex(self, index):
        """Add subindex.

        :Parameters:
          `index` : Index instance
              Index instance for inclusion.
        """
        if not isinstance(index, Index):
            raise ValueError("subindex has to be instance of Index")

        self.subindices.append(index)
        self._indices_dict[index.name] = index

    def remove_subindex(self, index_name):
        """Remove subindex (refered by name).

        :Parameters:
          `index` : Index name
              Index name to be removed.
        """
        index = self._indices_dict[index_name]
        self.subindices.remove(index)
        del self._indices_dict[index_name]

    def _print_info_one(self):
        if self.cheesecake.verbose:
            sys.stdout.write(self.get_info())
        print "%s  (%s)" % (pad_msg(index_class_to_name(self.name), self.value), self.details)

    def _print_info_many(self):
        max_value = self.max_value
        if max_value == 0:
            return

        percentage = int(ceil(float(self.value) / float(max_value) * 100))
        print pad_line("-")

        print pad_msg("%s INDEX (ABSOLUTE)" % self.name, self.value)
        msg = pad_msg("%s INDEX (RELATIVE)" % self.name, percentage)
        msg += "  (%d out of a maximum of %d points is %d%%)" %\
               (self.value, max_value, percentage)

        print msg
        print

    def print_info(self):
        """Print index name padded with dots, followed by value and details.
        """
        if self.subindices:
            self._print_info_many()
        else:
            self._print_info_one()

    def __getitem__(self, name):
        return self._indices_dict[name]

    def get_info(self):
        if self.subindices:
            return ''.join(map(lambda index: index.get_info(), self.subindices))
        return self.info

################################################################################
## Index that computes scores based on files and directories.
################################################################################

class OneOf(object):
    def __init__(self, *possibilities):
        self.possibilities = possibilities
    def __str__(self):
        return '/'.join(map(lambda x: str(x), self.possibilities))

def WithOptionalExt(name, extensions):
    """Handy way of writing Cheese rules for files with extensions.

    Instead of writing:
        >>> one_of = OneOf('readme', 'readme.html', 'readme.txt')

    Write this:
        >>> opt_ext = WithOptionalExt('readme', ['html', 'txt'])

    It means the same! (representation has a meaning)
        >>> str(one_of) == str(opt_ext)
        True
    """
    possibilities = [name]
    possibilities.extend(map(lambda x: name + '.' + x, extensions))

    return OneOf(*possibilities)

def Doc(name):
    return WithOptionalExt(name, ['html', 'txt', 'rst'])

class FilesIndex(Index):
    _used_rules = []

    def _compute_from_rules(self, files_list, package_dir, files_rules):
        self._used_rules = []
        files_count = 0
        value = 0

        for filename in files_list:
            if not is_empty(os.path.join(package_dir, filename)):
                score = self.get_score(os.path.basename(filename), files_rules)
                if score != 0:
                    value += score
                    files_count += 1

        return files_count, value

    def get_score(self, name, specs):
        for entry, value in specs.iteritems():
            if self.match_filename(name, entry):
                self.cheesecake.log.debug("%d points entry found: %s (%s)" % \
                                          (value, name, entry))
                return value

        return 0

    def get_not_used(self, files_rules):
        """Get only these of files_rules that didn't match during computation.

        >>> rules = {
        ...     Doc('readme'): 30,
        ...     OneOf(Doc('license'), Doc('copying')): 30,
        ...     'demo': 10,
        ... }
        >>> index = FilesIndex()
        >>> index._used_rules.append('demo')
        >>> map(lambda x: str(x), index.get_not_used(rules.keys()))
        ['license/license.html/license.txt/copying/copying.html/copying.txt', 'readme/readme.html/readme.txt']
        """
        return filter(lambda rule: rule not in self._used_rules,
                      files_rules)

    def match_filename(self, name, rule):
        """Check if `name` matches given `rule`.
        """
        def equal(x, y):
            x_root, x_ext = os.path.splitext(x)
            y_root, y_ext = os.path.splitext(y.lower())
            if x_root in [y_root.lower(), y_root.upper(), y_root.capitalize()] \
                   and x_ext in [y_ext.lower(), y_ext.upper()]:
                return True
            return False

        if rule in self._used_rules:
            return False

        if isinstance(rule, basestring):
            if equal(name, rule):
                self._used_rules.append(rule)
                return True
        elif isinstance(rule, OneOf):
            for poss in rule.possibilities:
                if self.match_filename(name, poss):
                    self._used_rules.append(rule)
                    return True

        return False

################################################################################
## Installability index.
################################################################################

class IndexUrlDownload(Index):
    """Give points for successful downloading of a package.
    """
    max_value = 25

    def compute(self, downloaded_from_url, package, url):
        if downloaded_from_url:
            self.details = "downloaded package %s from URL %s"  % (package, url)
            self.value = self.max_value
        else:
            self.value = 0

        return self.value

    def decide_before_download(self, cheesecake):
        return cheesecake.url

class IndexUnpack(Index):
    """Give points for successful unpacking of a package archive.
    """
    max_value = 25

    def compute(self, unpacked):
        if unpacked:
            self.details = "package unpacked successfully"
            self.value = self.max_value
        else:
            self.details = "package couldn't be unpacked"
            self.value = 0

        return self.value

class IndexUnpackDir(Index):
    """Check if package unpack directory resembles package archive name.
    """
    max_value = 15

    def compute(self, unpack_dir, original_package_name):
        self.details = "unpack directory is " + unpack_dir

        if original_package_name:
            self.details += " instead of the expected " + original_package_name
            self.value = 0
        else:
            self.details += " as expected"
            self.value = self.max_value

        return self.value

    def decide_after_download(self, cheesecake):
        return cheesecake.package_type != 'egg'

class IndexSetupPy(FilesIndex):
    """Reward packages that have setup.py file.
    """
    name = "setup.py"
    max_value = 25

    files_rules = {
        'setup.py': 25,
    }

    def compute(self, files_list, package_dir):
        setup_py_found, self.value = self._compute_from_rules(files_list, package_dir, self.files_rules)

        if setup_py_found:
            self.details = "setup.py found"
        else:
            self.details = "setup.py not found"

        return self.value

    def decide_after_download(self, cheesecake):
        return cheesecake.package_type != 'egg'

class IndexInstall(Index):
    """Check if package can be installed via "python setup.py" command.
    """
    max_value = 50

    def compute(self, installed, sandbox_install_dir):
        if installed:
            self.details = "package installed in %s" % sandbox_install_dir
            self.value = self.max_value
        else:
            self.details = "could not install package in %s" % sandbox_install_dir
            self.value = 0

        return self.value

    def decide_before_download(self, cheesecake):
        return not cheesecake.static_only

class IndexPyPIDownload(Index):
    """Check if package was successfully downloaded from PyPI
    and how far from it actual package was.

    Distance is number of links user has to follow to download
    a given software package.
    """
    max_value = 50
    distance_penalty = -5

    def compute(self, package, found_on_cheeseshop, found_locally, distance_from_pypi, download_url):
        if download_url:
            self.value = self.max_value

            self.details = "downloaded package " + package

            if not found_on_cheeseshop:
                if distance_from_pypi > 0:
                    self.value += (distance_from_pypi - 1) * self.distance_penalty
                    self.details += " following %d link" % distance_from_pypi

                    if distance_from_pypi > 1:
                        self.details += "s"
                        self.details += " from PyPI"
                    else:
                        self.details += " from " + download_url
            else:
                self.details += " directly from the Cheese Shop"
        else:
            if found_locally:
                self.details = "found on local filesystem"
            self.value = 0

        return self.value

    def decide_before_download(self, cheesecake):
        return cheesecake.name

class IndexGeneratedFiles(Index):
    """Lower score for automatically generated files that should
    not be present in a package.
    """
    generated_files_penalty = -20
    max_value = 0

    def compute(self, files_list):
        self.value = 0

        pyc_files = len(get_files_of_type(files_list, 'pyc'))
        pyo_files = len(get_files_of_type(files_list, 'pyo'))

        if pyc_files > 0 or pyo_files > 0:
            self.value += self.generated_files_penalty

        self.details = "%d .pyc and %d .pyo files found" % \
                                  (pyc_files, pyo_files)

        return self.value

    def decide_after_download(self, cheesecake):
        return cheesecake.package_type != 'egg'

class IndexInstallability(Index):
    name = "INSTALLABILITY"

    subindices = [
        IndexPyPIDownload,
        IndexUrlDownload,
        IndexUnpack,
        IndexUnpackDir,
        IndexSetupPy,
        IndexInstall,
        IndexGeneratedFiles,
    ]

################################################################################
## Documentation index.
################################################################################

class IndexRequiredFiles(FilesIndex):
    """Check for existence of important files, like README or INSTALL.
    """
    cheese_files = {
        Doc('readme'): 30,
        OneOf(Doc('license'), Doc('copying')): 30,

        OneOf(Doc('announce'), Doc('changelog'), Doc('changes')): 20,
        Doc('install'): 20,

        Doc('authors'): 10,
        Doc('faq'): 10,
        Doc('news'): 10,
        Doc('thanks'): 10,
        Doc('todo'): 10,
    }

    cheese_dirs = {
        OneOf('doc', 'docs'): 30,
        OneOf('test', 'tests'): 30,

        OneOf('demo', 'example', 'examples'): 10,
    }

    max_value = sum(cheese_files.values() + cheese_dirs.values())

    def compute(self, files_list, dirs_list, package_dir):
        # Inform user of files and directories the package is missing.
        def make_info(dictionary, what):
            missing = self.get_not_used(dictionary.keys())
            importance = {30: ' critical', 20: ' important'}

            positive_msg = "Package has%s %s: %s."
            negative_msg = "Package doesn't have%s %s: %s."

            for key in dictionary.keys():
                msg = positive_msg
                if key in missing:
                    msg = negative_msg
                self.add_info(msg % (importance.get(dictionary[key], ''), what, str(key)))

        # Compute required files.
        files_count, files_value = self._compute_from_rules(files_list, package_dir, self.cheese_files)
        make_info(self.cheese_files, 'file')

        # Compute required directories.
        dirs_count, dirs_value = self._compute_from_rules(dirs_list, package_dir, self.cheese_dirs)
        make_info(self.cheese_dirs, 'directory')

        self.value = files_value + dirs_value

        self.details = "%d files and %d required directories found" % \
                       (files_count, dirs_count)

        return self.value

class IndexDocstrings(Index):
    """Compute how many objects have relevant docstrings.
    """
    max_value = 100

    def compute(self, object_cnt, docstring_cnt):
        percent = 0
        if object_cnt > 0:
            percent = float(docstring_cnt)/float(object_cnt)

        # Scale the result.
        self.value = int(ceil(percent * self.max_value))

        self.details = "found %d/%d=%.2f%% objects with docstrings" %\
                 (docstring_cnt, object_cnt, percent*100)

        return self.value

class IndexFormattedDocstrings(Index):
    """Compute how many of existing docstrings include any formatting,
    like epytext or reST.
    """
    max_value = 30

    def compute(self, object_cnt, docformat_cnt):
        percent = 0
        if object_cnt > 0:
            percent = float(docformat_cnt)/float(object_cnt)

        # Scale the result.
        # We give 10p for 25% of formatted docstrings, 20p for 50% and 30p for 75%.
        self.value = 0
        if percent > 0.75:
            self.add_info("%.2f%% formatted docstrings found, which is > 75%% and is worth 30p." % (percent*100))
            self.value = 30
        elif percent > 0.50:
            self.add_info("%.2f%% formatted docstrings found, which is > 50%% and is worth 20p." % (percent*100))
            self.value = 20
        elif percent > 0.25:
            self.add_info("%.2f%% formatted docstrings found, which is > 25%% and is worth 10p." % (percent*100))
            self.value = 10
        else:
            self.add_info("%.2f%% formatted docstrings found, which is < 25%%, no points given." % (percent*100))

        self.details = "found %d/%d=%.2f%% objects with formatted docstrings" %\
                 (docformat_cnt, object_cnt, percent*100)

        return self.value

class IndexDocumentation(Index):
    name = "DOCUMENTATION"

    subindices = [
        IndexRequiredFiles,
        IndexDocstrings,
        IndexFormattedDocstrings,
    ]

################################################################################
## Code "kwalitee" index.
################################################################################

class IndexUnitTests(Index):
    """Compute unittest index as percentage of methods/functions
    that are exercised in unit tests.
    """
    max_value = 50

    def compute(self, files_list, functions, classes, package_dir):
        unittest_cnt = 0
        functions_tested = set()

        # Gather all function names called from test files.
        for testfile in get_files_of_type(files_list, 'test'):
            fullpath = os.path.join(package_dir, testfile)
            code = CodeParser(fullpath, self.cheesecake.log.debug)

            functions_tested = functions_tested.union(code.functions_called)

        for name in functions + classes:
            if name in functions_tested:
                unittest_cnt += 1
                self.cheesecake.log.debug("%s is unit tested" % name)

        functions_classes_cnt = len(functions) + len(classes)
        percent = 0
        if functions_classes_cnt > 0:
            percent = float(unittest_cnt)/float(functions_classes_cnt)

        # Scale the result.
        self.value = int(ceil(percent * self.max_value))

        self.details = "found %d/%d=%.2f%% unit tested classes/methods/functions." %\
                 (unittest_cnt, functions_classes_cnt, percent*100)

        return self.value

class IndexUnitTested(Index):
    """Check if the package has unit tests which can be easily found by
    any of known test frameworks.
    """
    max_value = 30

    def compute(self, doctests_count, unittests_count, files_list, classes, methods):
        unit_tested = False

        if doctests_count > 0:
            self.add_info("Package includes doctest tests.")
            unit_tested = True

        if unittests_count > 0:
            self.add_info("Package has tests that inherit from unittest.TestCase.")
            unit_tested = True

        if get_files_of_type(files_list, 'test'):
            self.add_info("Package has filenames which probably contain tests (in format test_* or *_test)")
            unit_tested = True

        for method in methods:
            if self._is_test_method(method):
                self.add_info("Some classes have setUp/tearDown methods which are commonly used in unit tests.")
                unit_tested = True
                break

        if unit_tested:
            self.value = self.max_value
            self.details = "has unit tests"
        else:
            self.value = 0
            self.details = "doesn't have unit tests"

        return self.value

    def _is_test_method(self, method):
        nose_methods = ['setup', 'setup_package', 'setup_module', 'setUp',
                        'setUpPackage', 'setUpModule',
                        'teardown', 'teardown_package', 'teardown_module',
                        'tearDown', 'tearDownModule', 'tearDownPackage']

        for test_method in nose_methods:
            if method.endswith(test_method):
                return True
        return False

class IndexPyLint(Index):
    """Compute pylint index of the whole package.
    """
    name = "pylint"
    max_value = 50

    disabled_messages = [
        'W0403', # relative import
        'W0406', # importing of self
    ]

    def compute(self, files_list, package_dir, pylint_max_execution_time):
        # See if pylint script location is set via environment variable
        pylint_location = os.environ.get("PYLINT", "pylint")

        # Maximum length of arguments (not very precise).
        max_arguments_length = 65536

        # Exclude __init__.py files from score as they cause pylint
        #     to fail with ImportError "Unable to find module for %s in %s".
        files_to_lint = filter(lambda name: not name.endswith('__init__.py'),
                               get_files_of_type(files_list, 'module'))

        # Switching cwd so that pylint works correctly regarding
        #     running it on individual modules.
        original_cwd = os.getcwd()

        # Note: package_dir may be a file if the archive contains a single file.
        # If this is the case, change dir to the parent dir of that file.
        if os.path.isfile(package_dir):
            package_dir = os.path.dirname(package_dir)

        os.chdir(package_dir)

        pylint_score = 0
        count = 0
        error_count = 0

        for filenames in generate_arguments(files_to_lint, max_arguments_length - len(self._pylint_args())):
            filenames =  ' '.join(filenames)
            self.cheesecake.log.debug("Running pylint on files: %s." % filenames)

            # Run pylint, but don't allow it to work longer than one minute.
            rc, output = run_cmd("%s %s --persistent=n %s" % (pylint_location, filenames, self._pylint_args()),
                                 max_timeout=pylint_max_execution_time)
            if rc:
                if output == 'Time exceeded':
                    # Raise and exception what will cause PyLint to be removed from list of indices
                    #   and thus won't affect the score.
                    self.cheesecake.log.debug("pylint exceeded maximum execution time of %d seconds and was terminated." % \
                                              pylint_max_execution_time)
                    raise OSError
                self.cheesecake.log.debug("encountered an error (%d):\n***\n%s\n***\n" % (rc, output))
                error_count += 1
            else:
                # Extract score from pylint output.
                s = re.search(r"Your code has been rated at (-?\d+\.\d+)/10",
                              output)
                if s:
                    pylint_score += float(s.group(1))
                    count += 1

        # Switching back to the original cwd.
        os.chdir(original_cwd)

        if count:
            pylint_score = float(pylint_score)/float(count)
            self.details = "pylint score was %.2f out of 10" % pylint_score
        elif error_count:
            self.details = "encountered an error during pylint execution"
        else:
            self.details = "no files to check found"

        # Assume scores below zero as zero for means of index value computation.
        if pylint_score < 0:
            pylint_score = 0
        self.value = int(ceil(pylint_score/10.0 * self.max_value))

        self.add_info("Score is %.2f/10, which is %d%% of maximum %d points = %d." %
                      (pylint_score, int(pylint_score*10), self.max_value, self.value))

        return self.value

    def decide_before_download(self, cheesecake):
        # Try to run the pylint script
        if not command_successful("pylint --version"):
            cheesecake.log.debug("pylint not properly installed, omitting pylint index.")
            return False

        return not cheesecake.lite

    @classmethod
    def _pylint_args(cls):
        try:
            import pylint.__pkginfo__
            version = map(int, pylint.__pkginfo__.version.split('.'))
            if version > (0, 21):
                disable_option = "disable-msg"
            else:
                disable_option = "disable"
            return ' '.join(map(lambda x: '--%s=%s' % (disable_option, x),
                    cls.disabled_messages))
        except ImportError:
            # pylint is not installed
            return ""

class IndexPEP8(Index):
    """Compute PEP8 index for the modules in the package.
    """
    name = "pep8"

    #
    # Max value is a number of possible pep8 errors times 2,
    #   plus number of possible pep8 warnings.
    #
    # Currently pep8 module support 15 errors:
    #   E101,
    #   E111, E112, E113,
    #   E201, E202, E203,
    #   E211,
    #   E221, E222,
    #   E301, E302, E303,
    #   E401,
    #   E501
    # and 4 warnings:
    #   W191,
    #   W291,
    #   W601,
    #   W602
    #
    max_value = 34

    error_score = -2
    warning_score = -1

    def compute(self, files_list, package_dir):
        files_to_score = get_files_of_type(files_list, 'module')
        if len(files_to_score) == 0:
            self.value = 0
            self.details = "no modules found"
            return self.value

        full_paths = [os.path.join(package_dir, file) for file in files_to_score]
        arglist = ["-qq"] + full_paths
        pep8.process_options(arglist)
        for file in files_to_score:
            fullpath = os.path.join(package_dir, file)
            pep8.input_file(fullpath)
        error_stats = pep8.get_error_statistics()
        warning_stats = pep8.get_warning_statistics()

        errors = len(error_stats)
        warnings = len(warning_stats)

        total_error_score = self.error_score * errors
        total_warning_score = self.warning_score * warnings

        score = total_error_score + total_warning_score
        self.value = self.max_value + score

        self.add_info("Errors:")
        self.add_info("Count   Details")
        for stat in error_stats:
            self.add_info(stat)
        self.add_info("pep8.py found %d error types; we're scoring %d per error type" % (errors, self.error_score))
        self.add_info("Error score: %d" % total_error_score)
        self.add_info("Warnings:")
        self.add_info("Count   Details")
        for stat in warning_stats:
            self.add_info(stat)
        self.add_info("pep8.py found %d warning types; we're scoring %d per warning type" % (warnings, self.warning_score))
        self.add_info("Warning score: %d" % total_warning_score)
        self.add_info("Total pep8 score: %d - %d = %d" % (self.max_value, abs(score), self.value))

        self.details = "pep8.py check: %d error types, %d warning types" % (errors, warnings)
        return self.value

    def decide_before_download(self, cheesecake):
        return cheesecake.with_pep8

class IndexCodeKwalitee(Index):
    name = "CODE KWALITEE"

    subindices = [
        #IndexUnitTests,
        IndexUnitTested,
        IndexPyLint,
        IndexPEP8,
    ]

################################################################################
## Main Cheesecake class.
################################################################################

class CheesecakeError(Exception):
    """Custom exception class for Cheesecake-specific errors.
    """
    pass


class CheesecakeIndex(Index):
    name = "Cheesecake"
    subindices = [
        IndexInstallability,
        IndexDocumentation,
        IndexCodeKwalitee,
    ]


class Step(object):
    """Single step during computation of package score.
    """
    def __init__(self, provides):
        self.provides = provides

    def decide(self, cheesecake):
        """Decide if step should be run.

        It checks if there's at least one index from current profile that need
        variables provided by this step. Override this method for other behaviour.
        """
        for provide in self.provides:
            if provide in cheesecake.index.requirements:
                return True
        return False

class StepByVariable(Step):
    """Step which is always run if given Cheesecake instance variable is true.
    """
    def __init__(self, variable_name, provides):
        self.variable_name = variable_name
        Step.__init__(self, provides)

    def decide(self, cheesecake):
        if getattr(cheesecake, self.variable_name, None):
            return True

        # Fallback to the default.
        return Step.decide(self, cheesecake)

class Cheesecake(object):
    """Computes 'goodness' of Python packages.

    Generates "cheesecake index" that takes into account things like:

        * whether the package can be downloaded
        * whether the package can be unpacked
        * whether the package can be installed into an alternate directory
        * existence of certain files such as README, INSTALL, LICENSE, setup.py etc.
        * existence of certain directories such as doc, test, demo, examples
        * percentage of modules/functions/classes/methods with docstrings
        * percentage of functions/methods that are unit tested
        * average pylint score for all non-test and non-demo modules
    """

    steps = {}

    package_types = {
        "tar.gz": untar_package,
        "tgz": untar_package,
        "zip": unzip_package,
        "egg": unegg_package,
    }

    def __init__(self,
                 keep_log                  = False,
                 lite                      = False,
                 logfile                   = None,
                 name                      = "",
                 path                      = "",
                 pylint_max_execution_time = None,
                 quiet                     = False,
                 sandbox                   = None,
                 static_only               = False,
                 url                       = "",
                 verbose                   = False,
                 with_pep8                 = False):
        """Initialize critical variables, download and unpack package,
        walk package tree.
        """
        self.name = name
        self.url = url
        self.package_path = path

        if self.name:
            self.package = self.name
        elif self.url:
            self.package = get_package_name_from_url(self.url)
        elif self.package_path:
            self.package = get_package_name_from_path(self.package_path)
        else:
            self.raise_exception("No package name, URL or path specified... exiting")

        # Setup a sandbox.
        self.sandbox = sandbox or tempfile.mkdtemp(prefix='cheesecake')
        if not os.path.isdir(self.sandbox):
            os.mkdir(self.sandbox)

        self.verbose = verbose
        self.quiet = quiet
        self.static_only = static_only
        self.lite = lite
        self.keep_log = keep_log
        self.with_pep8 = with_pep8
        self.pylint_max_execution_time = pylint_max_execution_time

        self.sandbox_pkg_file = ""
        self.sandbox_pkg_dir = ""
        self.sandbox_install_dir = ""

        # Configure logging as soon as possible.
        self.configure_logging(logfile)

        # Log missing data.
        self.log.debug("Using sandbox directory %s." % self.sandbox)

        # Setup Cheesecake index.
        self.index = CheesecakeIndex()

        self.index.decide_before_download(self)
        self.log.debug("Profile requirements: %s." % ', '.join(sorted(self.index.requirements)))

        # Get the package.
        self.run_step('get_pkg_from_pypi')
        self.run_step('download_pkg')
        self.run_step('copy_pkg')

        # Get package name and type.
        name_and_type = get_package_name_and_type(self.package, self.package_types.keys())

        if not name_and_type:
            msg = "Could not determine package type for package '%s'" % self.package
            msg += "\nCurrently recognized types: " + ", ".join(self.package_types.keys())
            self.raise_exception(msg)

        self.package_name, self.package_type = name_and_type
        self.log.debug("Package name: " + self.package_name)
        self.log.debug("Package type: " + self.package_type)

        # Make last indices decisions.
        self.index.decide_after_download(self)

        # Unpack package and list its files.
        self.run_step('unpack_pkg')
        self.run_step('walk_pkg')

        # Install package.
        self.run_step('install_pkg')

    def raise_exception(self, msg):
        """Cleanup, print error message and raise CheesecakeError.

        Don't use logging, since it can be called before logging has been setup.
        """
        self.cleanup(remove_log_file=False)

        msg += "\nDetailed info available in log file %s" % self.logfile

        raise CheesecakeError("Error: " + msg)

    def cleanup(self, remove_log_file=True):
        """Delete temporary directories and files that were created
        in the sandbox. At the end delete the sandbox itself.
        """
        if os.path.isfile(self.sandbox_pkg_file):
            self.log("Removing file %s" % self.sandbox_pkg_file)
            os.unlink(self.sandbox_pkg_file)

        def delete_dir(dirname):
            "Delete directory recursively and generate log message."
            if os.path.isdir(dirname):
                self.log("Removing directory %s" % dirname)
                rmtree(dirname)

        delete_dir(self.sandbox)

        if remove_log_file and not self.keep_log:
            # Close the log file descriptor before removing
            # (Linux doesn't care, but it matters on Windows).
            if self.logfile_descriptor:
                self.logfile_descriptor.close()

            if os.path.exists(self.logfile):
                os.unlink(self.logfile)

    def configure_logging(self, logfile=None):
        """Default settings for logging.

        If verbose, log goes to console, else it goes to logfile.
        log.debug and log.info goes to logfile.
        log.warn and log.error go to both logfile and stdout.
        """
        if logfile:
            self.logfile = logfile
        else:
            self.logfile = os.path.join(tempfile.gettempdir(), self.package + ".log")

        self.logfile_descriptor = open(str(self.logfile), 'w', buffering=1)
        logger.setconsumer('logfile', self.logfile_descriptor)
        logger.setconsumer('console', logger.STDOUT)
        logger.setconsumer('null', None)

        self.log = logger.MultipleProducer('cheesecake logfile')
        self.log.info = logger.MultipleProducer('cheesecake logfile')
        self.log.debug = logger.MultipleProducer('cheesecake logfile')
        self.log.warn = logger.MultipleProducer('cheesecake console')
        self.log.error = logger.MultipleProducer('cheesecake console')

    def run_step(self, step_name):
        """Run step if its decide() method returns True.
        """
        step = self.steps[step_name]
        if step.decide(self):
            step_method = getattr(self, step_name)
            step_method()

    steps['get_pkg_from_pypi'] = StepByVariable('name',
                                                ['download_url',
                                                 'distance_from_pypi',
                                                 'found_on_cheeseshop',
                                                 'found_locally',
                                                 'sandbox_pkg_file'])
    def get_pkg_from_pypi(self):
        """Download package using setuptools utilities.

        New attributes:
          download_url : str
              URL that package was downloaded from.
          distance_from_pypi : int
              How many hops setuptools had to make to download package.
          found_on_cheeseshop : bool
              Whenever package has been found on CheeseShop.
          found_locally : bool
              Whenever package has been already installed.
        """
        self.log.info("Trying to download package %s from PyPI using setuptools utilities" % self.name)

        try:
            from setuptools.package_index import PackageIndex
            from pkg_resources import Requirement
            from distutils import log
            from distutils.errors import DistutilsError
        except ImportError, e:
            msg = "setuptools is not installed and is required for downloading a package by name\n"
            msg += "You can download and process a package by its full URL via the -u or --url option\n"
            msg += "Example: python cheesecake.py --url=http://www.mems-exchange.org/software/durus/Durus-3.1.tar.gz"
            self.raise_exception(msg)

        def drop_setuptools_info(stdout, error=None):
            """Drop all setuptools output as INFO.
            """
            self.log.info("*** Begin setuptools output")
            map(self.log.info, stdout.splitlines())
            if error:
                self.log.info(str(error))
            self.log.info("*** End setuptools output")

        def fetch_package(mode):
            """Fetch package from PyPI.

            Mode can be one of:
              * 'pypi_source': get source package from PyPI
              * 'pypi_any': get source/egg package from PyPI
              * 'any': get package from PyPI or local filesystem

            Returns tuple (status, output), where `status` is True
            if fetch was successful and False if it failed. `output`
            is PackageIndex.fetch() return value.
            """
            if 'pypi' in mode:
                pkgindex = PackageIndex(search_path=[])
            else:
                pkgindex = PackageIndex()

            if mode == 'pypi_source':
                source = True
            else:
                source = False

            try:
                output = pkgindex.fetch(Requirement.parse(self.name),
                                        self.sandbox,
                                        force_scan=True,
                                        source=source)
                return True, output
            except DistutilsError, e:
                return False, e

        # Temporarily set the log verbosity to INFO so we can capture setuptools
        # info messages.
        old_threshold = log.set_threshold(log.INFO)
        old_stdout = sys.stdout
        sys.stdout = StdoutRedirector()

        # Try to get source package from PyPI first, then egg from PyPI, and if
        # that fails search in locally installed packages.
        for mode, info in [('pypi_source', "source package on PyPI"),
                           ('pypi_any', "egg on PyPI"),
                           ('any', "locally installed package")]:
            msg = "Looking for %s... " % info
            status, output = fetch_package(mode)
            if status and output:
                self.log.info(msg + "found!")
                break
            self.log.info(msg + "failed.")

        # Bring back old stdout.
        captured_stdout = sys.stdout.read_buffer()
        sys.stdout = old_stdout
        log.set_threshold(old_threshold)

        # If all runs failed, we must raise an error.
        if not status:
            drop_setuptools_info(captured_stdout, output)
            self.raise_exception("setuptools returned an error: %s\n" % str(output).splitlines()[0])

        # If fetch returned nothing, package wasn't found.
        if output is None:
            drop_setuptools_info(captured_stdout)
            self.raise_exception("Could not find distribution for " + self.name)

        # Defaults.
        self.download_url = ""
        self.distance_from_pypi = 0
        self.found_on_cheeseshop = False
        self.found_locally = False

        for line in captured_stdout.splitlines():
            s = re.search(r"Reading http(.*)", line)
            if s:
                inspected_url = s.group(1)
                if "python.org/pypi" not in inspected_url:
                    self.distance_from_pypi += 1
                continue
            s = re.search(r"Downloading (.*)", line)
            if s:
                self.download_url = s.group(1)
                break

        self.sandbox_pkg_file = output
        self.package = get_package_name_from_path(output)
        self.log.info("Downloaded package %s from %s" % (self.package, self.download_url))

        if os.path.isdir(self.sandbox_pkg_file):
            self.found_locally = True

        if "cheeseshop.python.org" in self.download_url:
            self.found_on_cheeseshop = True

    steps['download_pkg'] = StepByVariable('url',
                                           ['sandbox_pkg_file',
                                            'downloaded_from_url'])
    def download_pkg(self):
        """Use ``urllib.urlretrieve`` to download package to file in sandbox dir.
        """
        #self.log("Downloading package %s from URL %s" % (self.package, self.url))
        self.sandbox_pkg_file = os.path.join(self.sandbox, self.package)
        try:
            downloaded_filename, headers = urlretrieve(self.url, self.sandbox_pkg_file)
        except IOError, e:
            self.log.error("Error downloading package %s from URL %s"  % (self.package, self.url))
            self.raise_exception(str(e))
        #self.log("Downloaded package %s to %s" % (self.package, downloaded_filename))

        if headers.gettype() in ["text/html"]:
            f = open(downloaded_filename)
            if re.search("404 Not Found", "".join(f.readlines())):
                f.close()
                self.raise_exception("Got '404 Not Found' error while trying to download package ... exiting")
            f.close()

        self.downloaded_from_url = True

    steps['copy_pkg'] = StepByVariable('package_path',
                                       ['sandbox_pkg_file'])
    def copy_pkg(self):
        """Copy package file to sandbox directory.
        """
        self.sandbox_pkg_file = os.path.join(self.sandbox, self.package)
        if not os.path.isfile(self.package_path):
            self.raise_exception("%s is not a valid file ... exiting" % self.package_path)
        self.log("Copying file %s to %s" % (self.package_path, self.sandbox_pkg_file))
        shutil.copyfile(self.package_path, self.sandbox_pkg_file)

    steps['unpack_pkg'] = Step(['original_package_name',
                                'sandbox_pkg_dir',
                                'unpacked',
                                'unpack_dir'])
    def unpack_pkg(self):
        """Unpack the package in the sandbox directory.

        Check `package_types` attribute for list of currently supported
        archive types.

        New attributes:
          original_package_name : str
              Package name guessed from the package name. Will be set only
              if package name is different than unpacked directory name.
        """
        self.sandbox_pkg_dir = os.path.join(self.sandbox, self.package_name)
        if os.path.isdir(self.sandbox_pkg_dir):
            self.log("Directory %s exist - removing..." % self.sandbox_pkg_dir)
            rmtree(self.sandbox_pkg_dir)

        # Call appropriate function to unpack the package.
        unpack = self.package_types[self.package_type]
        self.unpack_dir = unpack(self.sandbox_pkg_file, self.sandbox)

        if self.unpack_dir is None:
            self.raise_exception("Could not unpack package %s ... exiting" % \
                                 self.sandbox_pkg_file)

        self.unpacked = True

        if self.unpack_dir != self.package_name:
            self.original_package_name = self.package_name
            self.package_name = self.unpack_dir

    steps['walk_pkg'] = Step(['dirs_list',
                              'docstring_cnt',
                              'docformat_cnt',
                              'doctests_count',
                              'unittests_count',
                              'files_list',
                              'functions',
                              'classes',
                              'methods',
                              'object_cnt',
                              'package_dir'])
    def walk_pkg(self):
        """Get package files and directories.

        New attributes:
          dirs_list : list
              List of directories package contains.
          docstring_cnt : int
              Number of docstrings found in all package objects.
          docformat_cnt : int
              Number of formatted docstrings found in all package objects.
          doctests_count : int
              Number of docstrings that include doctests.
          unittests_count : int
              Number of classes which inherit from unittest.TestCase.
          files_list : list
              List of files package contains.
          functions : list
              List of all functions defined in package sources.
          classes : list
              List of all classes defined in package sources.
          methods : list
              List of all methods defined in package sources.
          object_cnt : int
              Number of documentable objects found in all package modules.
          package_dir : str
              Path to project directory.
        """
        self.package_dir = os.path.join(self.sandbox, self.package_name)

        self.files_list, self.dirs_list = get_files_dirs_list(self.package_dir)

        self.object_cnt = 0
        self.docstring_cnt = 0
        self.docformat_cnt = 0
        self.doctests_count = 0
        self.functions = []
        self.classes = []
        self.methods = []
        self.unittests_count = 0

        # Parse all application files and count objects
        # (modules/classes/functions) and their associated docstrings.
        for py_file in get_files_of_type(self.files_list, 'module'):
            pyfile = os.path.join(self.package_dir, py_file)
            code = CodeParser(pyfile, self.log.debug)

            self.object_cnt += code.object_count()
            self.docstring_cnt += code.docstring_count()
            self.docformat_cnt += code.formatted_docstrings_count
            self.functions += code.functions
            self.classes += code.classes
            self.methods += code.methods
            self.doctests_count += code.doctests_count
            self.unittests_count += code.unittests_count

        # Log a bit of debugging info.
        self.log.debug("Found %d files: %s." % (len(self.files_list),
                                                ', '.join(self.files_list)))
        self.log.debug("Found %d directories: %s." % (len(self.dirs_list),
                                                      ', '.join(self.dirs_list)))

    steps['install_pkg'] = Step(['installed'])
    def install_pkg(self):
        """Verify that package can be installed in alternate directory.

        New attributes:
          installed : bool
              Describes whenever package has been succefully installed.
        """
        self.log.info("Trying to install package %s" % self.name)

        self.sandbox_install_dir = os.path.join(self.sandbox, "tmp_install_%s" % self.package_name)

        if self.package_type == 'egg':
            # Create dummy Python directories.
            mkdirs('%s/lib/python2.3/site-packages/' % self.sandbox_install_dir)
            mkdirs('%s/lib/python2.4/site-packages/' % self.sandbox_install_dir)

            environment = {'PYTHONPATH':
                           '%(sandbox)s/lib/python2.3/site-packages/:'\
                           '%(sandbox)s/lib/python2.4/site-packages/' % \
                           {'sandbox': self.sandbox_install_dir},
                           # Pass PATH to child process.
                           'PATH': os.getenv('PATH')}
            rc, output = run_cmd("easy_install --no-deps --prefix %s %s" % \
                                 (self.sandbox_install_dir,
                                  self.sandbox_pkg_file),
                                 environment)
        else:
            package_dir = os.path.join(self.sandbox, self.package_name)
            if not os.path.isdir(package_dir):
                package_dir = self.sandbox
            cwd = os.getcwd()
            os.chdir(package_dir)
            rc, output = run_cmd("python setup.py install --root=%s" % \
                                 self.sandbox_install_dir)
            os.chdir(cwd)

        if rc:
            self.log('*** Installation failed. Captured output:')
            # Stringify output as it may be an exception.
            for output_line in str(output).splitlines():
                self.log(output_line)
            self.log('*** End of captured output.')
        else:
            self.log('Installation into %s successful.' % \
                     self.sandbox_install_dir)
            self.installed = True

    def compute_cheesecake_index(self):
        """Compute overall Cheesecake index for the package by adding up
        specific indexes.
        """
        # Pass Cheesecake instance to the main Index object.
        cheesecake_index = self.index.compute_with(self)

        # Get max value *after* computing indices, because computing
        #   process can remove some indices from the list.
        max_cheesecake_index = self.index.max_value

        percentage = (cheesecake_index * 100) / max_cheesecake_index

        self.log.info("A given package can currently reach a MAXIMUM number of %d points" % max_cheesecake_index)
        self.log.info("Starting computation of Cheesecake index for package '%s'" % (self.package))

        # Print summary.
        if self.quiet:
            print "Cheesecake index: %d (%d / %d)" % (percentage,
                                                      cheesecake_index,
                                                      max_cheesecake_index)
        else:
            print
            print pad_line("=")
            print pad_msg("OVERALL CHEESECAKE INDEX (ABSOLUTE)", cheesecake_index)
            print "%s  (%d out of a maximum of %d points is %d%%)" % \
                  (pad_msg("OVERALL CHEESECAKE INDEX (RELATIVE)", percentage),
                   cheesecake_index,
                   max_cheesecake_index,
                   percentage)

        return cheesecake_index

################################################################################
## Command line.
################################################################################

def process_cmdline_args():
    """Parse command-line options.
    """
    parser = OptionParser()

    # Options for package retrieval.
    parser.add_option("-n", "--name", dest="name",
                      default="", help="package name (will be retrieved via setuptools utilities, if present)")
    parser.add_option("-p", "--path", dest="path",
                      default="", help="path of tar.gz/zip package on local file system")
    parser.add_option("-u", "--url", dest="url",
                      default="", help="package URL")

    # Output formatting options.
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                      default=False, help="only print Cheesecake index value (default=False)")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      default=False, help="verbose output (default=False)")

    # Index choice options.
    parser.add_option("--lite", action="store_true", dest="lite",
                      default=False, help="don't run time-consuming tests (default=False)")
    parser.add_option("-t", "--static", action="store_true", dest="static",
                      default=False, help="don't run any code from the package being tested (default=False)")
    parser.add_option("--with-pep8", action="store_true", dest="with_pep8",
                      default=False, help="check pep8 conformance")

    # Other options.
    parser.add_option("-l", "--logfile", dest="logfile",
                      default=None,
                      help="file to log all cheesecake messages")
    parser.add_option("-s", "--sandbox", dest="sandbox",
                      default=None,
                      help="directory where package will be unpacked "\
                           "(default is to use random directory inside %s)" % tempfile.gettempdir())
    parser.add_option("--keep-log", action="store_true", dest="keep_log",
                      default=False, help="don't remove log file even if run was successful")
    parser.add_option("--pylint-max-execution-time", action="store", dest="pylint_max_execution_time",
                      default=120, help="maximum time (in seconds) you allow pylint process to run (default=120)")

    parser.add_option("-V", "--version", action="store_true", dest="version",
                      default=False, help="Output cheesecake version and exit")

    (options, args) = parser.parse_args()
    return options

def main():
    """Display Cheesecake index for package specified via command-line options.
    """
    options = process_cmdline_args()
    keep_log = options.keep_log
    lite = options.lite
    logfile = options.logfile
    name = options.name
    path = options.path
    quiet = options.quiet
    sandbox = options.sandbox
    static_only = options.static
    url = options.url
    verbose = options.verbose
    version = options.version
    with_pep8 = options.with_pep8
    pylint_max_execution_time = int(options.pylint_max_execution_time)

    if version:
        print "Cheesecake version %s (rev. %s)" % (VERSION, __revision__)
        sys.exit(0)

    if not name and not url and not path:
        print "Error: No package name, URL or path specified (see --help)"
        sys.exit(1)

    try:
        c = Cheesecake(keep_log                  = keep_log,
                       lite                      = lite,
                       logfile                   = logfile,
                       name                      = name,
                       path                      = path,
                       pylint_max_execution_time = pylint_max_execution_time,
                       quiet                     = quiet,
                       sandbox                   = sandbox,
                       static_only               = static_only,
                       url                       = url,
                       verbose                   = verbose,
                       with_pep8                 = with_pep8)
        c.compute_cheesecake_index()
        c.cleanup()
    except CheesecakeError, e:
        print str(e)

if __name__ == "__main__":
    main()
