from mypydoc import guess_format, parse_docstring, YIELDS_ERROR, NAMED_ITEMS_ERROR

from typing import List

from mock import MagicMock, call

import pytest


def get_format(docstring):
    format = guess_format(docstring)
    return format(0, MagicMock())


def parse(docstring):
    format = get_format(docstring)
    params, result = format.do_parse(docstring)
    conformed = [(k, tuple(v)) for k, v in params.items()]
    if result is not None:
        conformed.append(('return', tuple(result)))
    return conformed


def convert(docstring, line=0):
    logger = MagicMock()
    return logger, parse_docstring(docstring, line, logger)


def test_basic():
    assert parse('''
:param path: The path of the :obj:`file` to wrap
:type path: str
:param basic_type: basic type description
:type basic_type: bool''') == [
        ('path', ('str', 2)),
        ('basic_type', ('bool', 4))
    ]


def test_complex():
    assert parse('''
:param complex: valid pep484 type description
:type complex: Union[Dict[str, int], str]
:param multiline: pep484 type description spanning multiple lines
:type multiline: Union[Dict[str,int],
    List[Tuple[str, int]]]
:param  whitespace: leading and trailing whitespace
:type  whitespace:   Union[Dict[str, int], str]   
:param leading_newline: leading newline
:type leading_newline:
    Union[Dict[str, int], str]   
    ''') == [
        ('complex', ('Union[Dict[str, int], str]', 2)),
        ('multiline', ('Union[Dict[str,int], List[Tuple[str, int]]]', 4)),
        ('whitespace', ('Union[Dict[str, int], str]', 7)),
        ('leading_newline', ('Union[Dict[str, int], str]', 10))
    ]


def test_custom_type():
    assert parse('''
:param custom_type: The :class:`CustomType` instance to wrap
:type custom_type: CustomType''') == [
        ('custom_type', ('CustomType', 2))
    ]


def test_missing_args():
    assert parse('''
:param missing_type: parameter that has no type pair
:type  missing_param: bool''') == [
        ('missing_param', ('bool', 2)),
    ]


def test_returns():
    assert parse('''
:returns: simple return value
:rtype: bool''') == [
        ('return', ('bool', 2)),
    ]


def test_numpydoc():
    s = '''
        One line summary.

        Extended description.

        Parameters
        ----------
        arg1 : Any
            Description of `arg1`
        arg2 : Union[str, int]
            Description of `arg2`

        Returns
        -------
        str
            Description of return value.
    '''
    format = get_format(s)
    assert format.name == 'numpy'
    assert format.to_rest(s) == '''\
One line summary.

Extended description.

:param arg1: Description of arg1
:type arg1: Any
:param arg2: Description of arg2
:type arg2: Union[str, int]

:returns: Description of return value.
:rtype: str
'''


def test_numpydoc_yields():
    s = '''
        Yields
        ------
        str
            Description of return value.
    '''
    format = get_format(s)
    assert format.name == 'numpy'
    assert format.to_rest(s) == '''\
:Yields: *str* -- Description of return value.
'''
    ctx, result = convert(s)
    # note: warning is misspelled in mypy
    assert ctx.warning.call_args_list == [
        call(YIELDS_ERROR, extra={'column': 0, 'line': 1})
    ]


def test_numpydoc_named_result():
    s = '''
        Returns
        -------
        result1: str
            Description of first item
    '''
    format = get_format(s)
    assert format.name == 'numpy'
    assert format.to_rest(s) == '''\
:returns: **result1** -- Description of first item
:rtype: str
'''
    ctx, result = convert(s)
    assert ctx.error.call_args_list == []
    assert parse(s) == [
        ('return', ('str', 2))
    ]


def test_numpydoc_tuple_result():
    s = '''
        Returns
        -------
        result1: str
            Description of first item
        result2: bool
            Description of second item
    '''
    format = get_format(s)
    assert format.name == 'numpy'
    assert format.to_rest(s) == '''\
:returns: * **result1** (*str*) -- Description of first item
          * **result2** (*bool*) -- Description of second item
'''
    ctx, result = convert(s)
    # note: warning is misspelled in mypy
    assert ctx.warning.call_args_list == [
        call(NAMED_ITEMS_ERROR, extra={'column': 0, 'line': 1})
    ]


@pytest.mark.skip('only pep484 docstrings are supported')
def test_transform_union():
    assert parse('''
:param union_or: type union using 'or'
:type union_or: int or float or str
:param union_pipe: type union using '|'
:type union_pipe: int | float|str''') == [
        ('union_or', 'Union[int, float, str]'),
        ('union_pipe', 'Union[int, float, str]'),
    ]


@pytest.mark.skip('only pep484 docstrings are supported')
def test_transform_lower_dict():
    assert parse('''
:param lower_dict: lower-case dict (pycharm style)
:type lower_dict: dict[str, int]''') == [
        ('lower_dict', 'Dict[str, int]'),
    ]


@pytest.mark.skip('only pep484 docstrings are supported')
def test_transform_optional():
    assert parse('''
:param optional: optional parameter
:type optional: str or int, optional''') == [
        ('optional', 'Optional[Union[str, int]]'),
    ]


@pytest.mark.skip('only pep484 docstrings are supported')
def test_transform_yields_with_description():
    """Test output produced when using Yields in numpy or google format
    """
    assert parse('''
:Yields: *bool* -- Description of return value.''') == [
        ('return', 'Iterable[bool]')
    ]


@pytest.mark.skip('only pep484 docstrings are supported')
def test_transform_yields_without_description():
    """Test output produced when using Yields in numpy or google format
    """
    assert parse('''
:Yields: *bool*''') == [
        ('return', 'Iterable[bool]')
    ]


@pytest.mark.skip('only pep484 docstrings are supported')
def test_transform_yields_tuple():
    """Test output produced when using named values in a Yields section in
    numpy or google format"""
    assert parse('''
:Yields: * **result1** (*str*) -- Description of first item
         * **result2** (*bool*) -- Description of second item
''') == [
        ('return', 'Iterable[Tuple[str, bool]]')
    ]


@pytest.mark.skip('only pep484 docstrings are supported')
def test_returns_tuple():
    """Test output produced when using named values in a Returns section in
    numpy or google format"""
    assert parse('''
:returns: * **result1** (*str*) -- Description of first item
          * **result2** (*bool*) -- Description of second item
''') == [
        ('return', 'Tuple[str, bool]')
    ]
