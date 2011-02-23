import doctest
import os
import re

import logger
from model import System, Module, Class, Function, parseFile, processModuleAst


# Python 2.3/sel.4 compatibilty hacks.
if getattr(doctest, 'DocTestParser', False):
    # Python 2.4 have DocTestParser class.
    get_doctests = doctest.DocTestParser().get_examples
else:
    # Python 2.3 have _extract_examples function.
    get_doctests = doctest._extract_examples


def compile_regex(pattern, user_map=None):
    """Compile a regex pattern using default or user mapping.
    """

    # Handy regular expressions.
    mapping = {'ALPHA': r'[-.,?!\w]', 'WORD': r'[-.,?!\s\w]',
                       'START': r'(^|\s)', 'END': r'([.,?!\s]|$)'}

    if user_map:
        mapping = mapping.copy()
        mapping.update(user_map)

    def sub(text, mapping):
        for From, To in mapping.iteritems():
            text = text.replace(From, To)
        return text

    pattern = sub(pattern, mapping)

    return re.compile(pattern, re.LOCALE | re.VERBOSE)

def inline_markup(start, end=None, mapping=None):
    if end is None:
        end = start
    return compile_regex(r'''(START  %(start)s  ALPHA  %(end)s  END) |
           (START  %(start)s  ALPHA  WORD*  ALPHA  %(end)s  END)'''\
                         % {'start': start, 'end': end}, mapping)

def line_markup(start, end=None):
    return inline_markup(start, end, mapping={'ALPHA': r'[-.,?!\s\w]',
                                              'START': r'(\n|^)[\ \t]*',
                                              'END': r''})

supported_formats = {
    # reST refrence: http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html
    'reST': [
        inline_markup(r'\*'), # emphasis
        inline_markup(r'\*\*'), # strong
        inline_markup(r'``'), # inline
        inline_markup(r'\(', r'_\)', # hyperlink
                      {'ALPHA': r'\w', 'WORD': r'[-.\w]'}),
        inline_markup(r'\(`', r'`_\)'), # long hyperlink
        line_markup(r':'), # field
        line_markup(r'[*+-]', r''), # unordered list
        line_markup(r'((\d+) | ([a-zA-Z]+) [.\)])', r''), # ordered list
        line_markup(r'\(  ((\d+)  |  ([a-zA-Z]+))  \)', r''), # ordered list
    ],

    # epytext reference: http://epydoc.sourceforge.net/epytext.html
    'epytext': [
        re.compile(r'[BCEGILMSUX]\{.*\}'), # inline elements
        line_markup(r'@[a-z]+([\ \t][a-zA-Z]+)?:', r''), # fields
        line_markup(r'-', r''), # unordered list
        line_markup(r'\d+(\.\d+)*', r''), # ordered list
    ],

    # javadoc reference: http://java.sun.com/j2se/1.4.2/docs/tooldocs/solaris/javadoc.html
    'javadoc': [
        re.compile(r'<[a-zA-z]+[^>]*>'), # HTML elements
        line_markup(r'@[a-z][a-zA-Z]*\s', r''), # normal tags
        re.compile(r'{@  ((docRoot) | (inheritDoc) | (link) | (linkplain) |'\
                    ' (value))  [^}]*  }', re.VERBOSE), # special tags
    ],

    # sphinx reference: http://sphinx.pocoo.org/rest.html
    'sphinx': [
        inline_markup(r'``'), # inline
        re.compile(r':param [a-zA-Z_]+:'), # param
        re.compile(r':[a-z]+:'), # class, module, function references
        re.compile(r'\.\. [a-z]+::'), # directives
    ],
}


def use_format(text, format):
    """Return True if text includes given documentation format
    and False otherwise.

    See supported_formats for list of known formats.
    """
    for pattern in supported_formats[format]:
        if re.search(pattern, text):
            return True

    return False


class CodeParser(object):
    """Information about the structure of a Python module.

    * Collects modules, classes, methods, functions and associated docstrings
    * Based on mwh's docextractor.model module
    """
    def __init__(self, pyfile, log=None):
        """Initialize Code Parser object.

        :Parameters:
          `pyfile` : str
              Path to a Python module to parse.
          `log` : logger.Producer instance
              Logger to use during code parsing.
        """
        if log:
            self.log = log.codeparser
        else:
            self.log = logger.default.codeparser
        self.modules = []
        self.classes = []
        self.methods = []
        self.method_func = []
        self.functions = []
        self.docstrings = [] # objects that have docstrings
        self.docstrings_by_format = {}
        self.formatted_docstrings_count = 0
        self.doctests_count = 0
        self.unittests_count = 0

        # Initialize lists of format docstrings.
        for format in supported_formats:
            self.docstrings_by_format[format] = []

        (path, filename) = os.path.split(pyfile)
        (module, ext) = os.path.splitext(filename)
        self.log("Inspecting file: " + pyfile)

        self.system = System()
        try:
            processModuleAst(parseFile(pyfile), module, self.system)
        except Exception, e:
            self.log("Code parsing error occured:\n***\n%s\n***" % str(e))
            return

        for obj in self.system.orderedallobjects:
            fullname = obj.fullName()
            if isinstance(obj, Module):
                self.modules.append(fullname)
            if isinstance(obj, Class):
                if 'unittest.TestCase' in obj.bases or 'TestCase' in obj.bases:
                    self.unittests_count += 1
                self.classes.append(fullname)
            if isinstance(obj, Function):
                self.method_func.append(fullname)
            if isinstance(obj.docstring, str) and obj.docstring.strip():
                self.docstrings.append(fullname)
                # Check docstring for known documenation formats.
                formatted = False
                for format in supported_formats:
                    if use_format(obj.docstring, format):
                        self.docstrings_by_format[format].append(fullname)
                        formatted = True
                if formatted:
                    self.formatted_docstrings_count += 1
                else:
                    self.log(str(fullname) + " has unformated docstrings")

                # Check if docstring include any doctests.
                if get_doctests(obj.docstring):
                    self.doctests_count += 1

        for method_or_func in self.method_func:
            method_found = 0
            for cls in self.classes:
                if method_or_func.startswith(cls):
                    self.methods.append(method_or_func)
                    method_found = 1
                    break
            if not method_found:
                self.functions.append(method_or_func)
                
        self.log("modules: " + ",".join(self.modules))
        self.log("classes: " + ",".join(self.classes))
        self.log("methods: " + ",".join(self.methods))
        self.log("functions: " + ",".join(self.functions))
        self.log("docstrings: %s" % self.docstrings_by_format)
        self.log("number of doctests: %d" % self.doctests_count)

    def object_count(self):
        """Return number of objects found in this module.

        Objects include:
        * module
        * classes
        * methods
        * functions
        """
        module_count = len(self.modules)
        cls_count = len(self.classes)
        method_count = len(self.methods)
        func_count = len(self.functions)
        return module_count + cls_count + method_count + func_count

    def docstring_count(self):
        """Return number of docstrings found in this module.
        """
        return len(self.docstrings)

    def docstring_count_by_type(self, type):
        """Return number of docstrings of given type found in this module.
        """
        return len(self.docstrings_by_format[type])

    def _functions_called(self):
        """Return list of functions called by functions/methods
        defined in this module.
        """
        return self.system.func_called.keys()

    functions_called = property(_functions_called)
