"""
Module-level docs
"""

from __future__ import absolute_import, print_function


def basic(one, two, three, four, five, six):
    # type: (Union[str, int], str, Any, Any, bool, int) -> bool
    """
    Parameters
    ----------
    one : Union[str, int]
        description of one
    two : str
        description of two
        that spans multiple lines
    four
        omitted type
    five : bool
        description
        with

        a line break
    six : int

    Return
    ------
    bool
    """


def star_args(one, *two, **three):
    # type: (Union[str, int], *str, **Any) -> bool
    """
    Parameters
    ----------
    one : Union[str, int]
    two : str

    Return
    ------
    bool
    """


def star_args2(one, *two, **three):
    # type: (Union[str, int], *str, **Any) -> bool
    """
    Parameters
    ----------
    one : Union[str, int]
    two : *str

    Return
    ------
    bool
    """


def skiptype(one, two, three):
    # notype
    """
    Use # notype comment to skip type comment generation

    Parameters
    ----------
    one : Union[str, int]
    two : str

    Return
    ------
    bool
    """


def no_doc_types(one, *two, **three):
    """
    Docstring with no types
    """


def no_docs(one, *two, **three):
    pass


def existing_type_comment(one, two, three):
    # type: (Union[str, int], str, Any) -> bool
    """
    Existing type comments should be overwritten

    Parameters
    ----------
    one : Union[str, int]
    two : str

    Return
    ------
    bool
    """


def existing_comment(one, two, three):
    # this comment should be preserved
    """
    Parameters
    ----------
    one : Union[str, int]
    two : str

    Return
    ------
    bool
    """


def default_return_type(one):
    # type: (str) -> None
    """
    Description of foo

    Parameters
    ----------
    one : str
    """


def returns_tuple():
    """
    Verbose tuple return documentation

    Returns
    -------
    one : Union[str, int]
        description of one
    two : str
        description of two
        that spans multiple lines
    four
        omitted colon defaults to type
    five : bool
        description
        with

        a line break
    six : int
    """


def yields():
    """
    Yields
    ------
    str
    """


def yields_tuple():
    """
    Verbose tuple return documentation

    Yields
    ------
    one : Union[str, int]
        description of one
    two : str
        description of two
        that spans multiple lines
    four
        omitted colon defaults to type
    five : bool
        description
        with

        a line break
    six : int
    """


class BasicClass:
    def foo(self, one, two, three):
        # type: (Union[str, int], str, Any) -> bool
        """
        Parameters
        ----------
        one : Union[str, int]
        two : str

        Return
        ------
        bool
        """


def function_self(self, one, two, three):
    # type: (Any, Union[str, int], str, Any) -> bool
    """
    A function with a first argument named self should document self

    Parameters
    ----------
    one : Union[str, int]
    two : str

    Return
    ------
    bool
    """


class InitDocsAtClassLevel:
    """
    Argument documentation at the class-level should be applied to __init__

    Parameters
    ----------
    one : Union[str, int]
    two : str
    """
    def __init__(self, one, two, three):
        # type: (Union[str, int], str, Any) -> None
        pass
