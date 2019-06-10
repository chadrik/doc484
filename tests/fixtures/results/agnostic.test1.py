"""
Module-level docs
"""

from __future__ import absolute_import, print_function


def no_doc_types(one, *two, **three):
    """
    Docstring with no types

    No type comment should be generated
    """


def no_docs(one, *two, **three):
    pass


def nodocs_no_types(arg1, arg2):
    pass


def nodocs_with_types(arg1, arg2):
    # type: (int, str) -> int
    pass


def docs_with_types(arg1, arg2):
    # type: (int, str) -> int
    """
    Docstring with no types

    The type comment should be preserved
    """


def nodocs_one_line(x): return x
