"""
Docstring for module1

@summary: Code used inside test_code_parser.py unit test.
"""

class Class1:
    """
    Docstring for Class1

    @see how.Tests#are(performed)
    """

    def __init__(self):
        """
        Methods starting with __ are not skipped
        """
        pass

    def __another_method__(self):
        """Should not be skipped"""
        pass

    def method1(self):
        """Docstring for method1"""
        pass

    def method2(self):
        "Docstring for method2"
        pass

    def method3(self):
        """
        Docstring for method3
        """
        pass

    def method4(self):
        # No docstring
        pass

    def method5(self):
        """Method with few definitions.

        :Word: And its definition.
        """
        pass

class Class2:

    """
    Docstring one line apart from Class2
    """
    pass


def func1():
    """Docstring for func1"""
    return

def func2():
    "Docstring for func2"
    return

def func3():
    """
    Docstring for func3
    """
    return

def func4():
    # No docstring
    return

def __func5__(self):
    """
    Functions starting with __ are not skipped
    """
    return

def func6():
    """
    """
    pass

def func7():
    "Time to get *a bit* of reST."
    pass

def func8(argument):
    """This is test function for the epytext parser.

    @param argument: And you really can't say if this is
        epytext or javadoc! We count both.
    """
    pass


class Class3(object):
    """
    New-style class with epytext link: U{http://pycheesecake.org}.
    """
    pass


def outer_function(*args):
    x = 42

    def inner_function():
        """Short docstring."""
        pass

    return x
