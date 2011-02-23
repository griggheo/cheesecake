import os

import _path_cheesecake
from _helper_cheesecake import set, DATA_PATH

from cheesecake.codeparser import CodeParser, use_format


class TestCodeParser(object):
    def setUp(self):
        self.code1 = CodeParser(os.path.join(DATA_PATH, "module1.py"))

    def test_modules(self):
        assert self.code1.modules == ["module1"]

    def test_classes(self):
        assert self.code1.classes == [
            "module1.Class1",
            "module1.Class2",
            "module1.Class3",
        ]

    def test_methods(self):
        assert self.code1.methods == [
            "module1.Class1.__init__",
            "module1.Class1.__another_method__",
            "module1.Class1.method1",
            "module1.Class1.method2",
            "module1.Class1.method3",
            "module1.Class1.method4",
            "module1.Class1.method5",
        ]

    def test_functions(self):
        assert self.code1.functions == [
            "module1.func1",
            "module1.func2",
            "module1.func3",
            "module1.func4",
            "module1.__func5__",
            "module1.func6",
            "module1.func7",
            "module1.func8",
            "module1.outer_function",
            "module1.outer_function.inner_function",
        ]

    def test_count(self):
        assert self.code1.object_count() == 21
        assert self.code1.docstring_count() == 17
        assert self.code1.docstring_count_by_type('reST') == 2
        assert self.code1.docstring_count_by_type('epytext') == 3
        assert self.code1.docstring_count_by_type('javadoc') == 2

    def test_docstrings(self):
        objects_with_docstrings = [
            "module1",
            "module1.Class1",
            "module1.Class2",
            "module1.Class3",
            "module1.Class1.__init__",
            "module1.Class1.__another_method__",
            "module1.Class1.method1",
            "module1.Class1.method2",
            "module1.Class1.method3",
            "module1.Class1.method5",
            "module1.func1",
            "module1.func2",
            "module1.func3",
            "module1.__func5__",
            "module1.func7",
            "module1.func8",
            "module1.outer_function.inner_function",
        ]
        objects_with_rest_docstrings = [
            "module1.Class1.method5",
            "module1.func7",
        ]
        objects_with_epytext_docstrings = [
            "module1",
            "module1.Class3",
            "module1.func8",
        ]
        objects_with_javadoc_docstrings = [
            "module1.Class1",
            "module1.func8", # intentional overlap with epytext
        ]

        print self.code1.docstrings

        assert set(objects_with_docstrings) == set(self.code1.docstrings)
        assert set(objects_with_rest_docstrings) == set(self.code1.docstrings_by_format['reST'])
        assert set(objects_with_epytext_docstrings) == set(self.code1.docstrings_by_format['epytext'])
        assert set(objects_with_javadoc_docstrings) == set(self.code1.docstrings_by_format['javadoc'])


class TestDocumentationFormats(object):
    def _do_it(self, format, valid, invalid):
        for test in valid:
            print "Trying '%s'" % test
            assert use_format(test, format) is True

        for test in invalid:
            print "Trying '%s'" % test
            assert use_format(test, format) is False

    def test_reST(self):
        valid_test_strings = [
            "String with *emphasis*.",
            "*Multi-word emphasis.*",
            "How about testing **strong string**?",
            "Some *noisy!* punctuation",
            "**characters?**, in the way.",
            "Don't forget ``inline literals``.",
            "This is reST (hyperlink_).",
            "This is (`quite long hyperlink`_).",
            "* Bullet\n* List\n",
            "+ Another\n+ Bullet\n+ List\n",
            "1. Ordered\n2. List\n",
            "  a) Another\n  b) ordered\n  c) list\n",
            " (a) one\n (b) more",
            ":Field: list\n:indeed: it is\n",
        ]
        invalid_test_strings = [
            "Plain string.",
            "Do some math: 2 * 2a* 2 = 8a",
            "Not*really*strong.",
            "Interpreted `text` is widely used as quotes, so exclude it.",
            "Not a :field:.",
        ]

        self._do_it('reST', valid_test_strings, invalid_test_strings)

    def test_epytext(self):
        valid_test_strings = [
            "- Bullet\n- List\n",
            "1. Ordered\n2. List\n",
            "1.1 Few points\n1.2 To remember\n",
            "Some I{italics} here.",
            "And a small bit of C{code}.",
            "@param self: You know what it means.",
            "@return: Return a long\ndescription.",
        ]
        invalid_test_strings = [
            "Aha - This is not an unordered list.",
            "email@example.com",
            "Short Python dictionary: {0: 'zero', 1: 'one'}.",
            "@ not a field: at all",
        ]

        self._do_it('epytext', valid_test_strings, invalid_test_strings)

    def test_javadoc(self):
        valid_test_strings = [
            'Inline <a href="{@docRoot}/html/documents/">are ugly</a>!',
            "Call {@link #test_javadoc(object) test_javadoc} method.",
            '@see Why#java(sucks)',
        ]
        invalid_test_strings = [
            "Normal text.",
            "mail.address@example.com",
            "Mathematical: a < b < c while x > y.",
            "@it: is not javadoc, but epytext!",
        ]

        self._do_it('javadoc', valid_test_strings, invalid_test_strings)
