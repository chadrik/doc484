"""
Module-level docs
"""

from __future__ import absolute_import, print_function


def basic(one, two, three, four, _five, six_):
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
    _five : bool
        description
        with

        a line break
    six_ : int

    Returns
    -------
    bool
        True if successful, False otherwise
    """


def star_args(one, *two, **three):
    # type: (Union[str, int], *str, **Any) -> bool
    """
    Parameters
    ----------
    one : Union[str, int]
    two : str

    Returns
    -------
    bool
    """


def star_args2(one, *two, **three):
    # type: (Union[str, int], *str, **Any) -> bool
    """
    Parameters
    ----------
    one : Union[str, int]
    two : *str

    Returns
    -------
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

    Returns
    -------
    bool
    """


def no_doc_types(one, *two, **three):
    """
    Docstring with no types
    """


def no_docs(one, *two, **three):
    pass


def any_doc_types(one, *two, **three):
    # type: (Any, *Any, **Any) -> Any
    """
    Docstring with explicit Any types triggers comment generation

    Parameters
    ----------
    one : Any
    two : Any

    Returns
    -------
    Any
    """


def existing_type_comment(one, two, three):
    # type: (Union[str, int], str, Any) -> bool
    """
    Existing type comments should be overwritten

    Parameters
    ----------
    one : Union[str, int]
    two : str

    Returns
    -------
    bool
    """


def existing_type_comment_any(one, two, three):
    # type: (Any, Any, Any) -> Any
    """
    Existing type comments should be overwritten, even with Any types

    Parameters
    ----------
    one : Any
    two : Any

    Returns
    -------
    Any
    """


def existing_comment(one, two, three):
    # type: (Union[str, int], str, Any) -> bool
    # this comment should be preserved
    """
    Parameters
    ----------
    one : Union[str, int]
    two : str

    Returns
    -------
    bool
    """


def default_return_type(one):
    # type: (str) -> None
    """
    When no return type is specified, the default type can be globally
    configured.

    Parameters
    ----------
    one : str
    """


def returns_tuple():
    # type: () -> Tuple[Union[str, int], str, four, bool, int]
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
        omitted type
    _five : bool
        description
        with

        a line break
    six_ : int
    """


def yields():
    # type: () -> Iterator[str]
    """
    Yields
    ------
    str
    """


def yields_tuple():
    # type: () -> Iterator[Tuple[Union[str, int], str, four, bool, int]]
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
        omitted type
    _five : bool
        description
        with

        a line break
    six_ : int
    """


class BasicClass:
    def foo(self, one, two, three):
        # type: (Union[str, int], str, Any) -> bool
        """
        Parameters
        ----------
        one : Union[str, int]
        two : str

        Returns
        -------
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

    Returns
    -------
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


def nodocs_no_types(arg1, arg2):
    pass


def nodocs_with_types(arg1, arg2):
    # type: (int, str) -> int
    pass
