from __future__ import absolute_import, print_function

from main import convert_string


def test_convert():
    input = '''\
"""
Module-level docs
"""

def foo(one, two, three):
    """
    Parameters
    ----------
    one : Union[str, int]
    two : str
    
    Return
    ------
    bool
    """
    pass
'''
    output = convert_string(input)

    expected = '''\
"""
Module-level docs
"""

def foo(one, two, three):
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
    pass
'''
    assert output == expected

