from doc484.formats import guess_format, parse_docstring, YIELDS_ERROR, NAMED_ITEMS_ERROR

from typing import List

from mock import MagicMock, call

import pytest


def get_format(docstring, options=None):
    format = guess_format(docstring)
    return format(0, logger=MagicMock(), options=options)


def parse(docstring, options=None):
    format = get_format(docstring, options=options)
    params, result = format.parse(docstring)
    conformed = [(k, tuple(v)) for k, v in params.items()]
    if result is not None:
        conformed.append(('return', tuple(result)))
    return conformed


def convert(docstring, line=0, options=None):
    logger = MagicMock()
    return logger, parse_docstring(docstring, line=line, logger=logger,
                                   options=options)


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
:param complex: valid doc484 type description
:type complex: Union[Dict[str, int], str]
:param multiline: doc484 type description spanning multiple lines
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


def test_missing_returns():
    assert parse('''
:returns:
:rtype:''') == []


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

:param arg1:
:type arg1: Any
:param arg2:
:type arg2: Union[str, int]

:returns:
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
:Yields: *str*
'''
    ctx, result = convert(s)
    assert ctx.warning.call_args_list == [
        call(YIELDS_ERROR,
             extra={'column': 0, 'line': 1, 'file': '<string>'})
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
:returns: **result1**
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
            Description with (items, in) parentheses
        result2: bool
        result3 : Dict[str, int]
            Description of third item
            That trails to next line
        other stuff that is not return value.
    '''
    format = get_format(s)
    assert format.name == 'numpy'
    print(format.to_rest(s))
    assert format.to_rest(s) == '''\
:returns: * **result1** (*str*)
          * **result2** (*bool*)
          * **result3** (*Dict[str, int]*)
          * *other stuff that is not return value.*
'''
    ctx, result = convert(s, options={'allow_named_results': False})
    assert ctx.warning.call_args_list == [
        call(NAMED_ITEMS_ERROR,
             extra={'column': 0, 'line': 1, 'file': '<string>'})
    ]
    assert parse(s, options={'allow_named_results': True}) == [
        ('return', ('Tuple[str, bool, Dict[str, int]]', 1))
    ]


@pytest.mark.skip('only doc484 docstrings are supported')
def test_transform_union():
    assert parse('''
:param union_or: type union using 'or'
:type union_or: int or float or str
:param union_pipe: type union using '|'
:type union_pipe: int | float|str''') == [
        ('union_or', 'Union[int, float, str]'),
        ('union_pipe', 'Union[int, float, str]'),
    ]


@pytest.mark.skip('only doc484 docstrings are supported')
def test_transform_lower_dict():
    assert parse('''
:param lower_dict: lower-case dict (pycharm style)
:type lower_dict: dict[str, int]''') == [
        ('lower_dict', 'Dict[str, int]'),
    ]


@pytest.mark.skip('only doc484 docstrings are supported')
def test_transform_optional():
    assert parse('''
:param optional: optional parameter
:type optional: str or int, optional''') == [
        ('optional', 'Optional[Union[str, int]]'),
    ]


@pytest.mark.skip('only doc484 docstrings are supported')
def test_transform_yields_with_description():
    """Test output produced when using Yields in numpy or google format
    """
    assert parse('''
:Yields: *bool* -- Description of return value.''') == [
        ('return', 'Iterable[bool]')
    ]


@pytest.mark.skip('only doc484 docstrings are supported')
def test_transform_yields_without_description():
    """Test output produced when using Yields in numpy or google format
    """
    assert parse('''
:Yields: *bool*''') == [
        ('return', 'Iterable[bool]')
    ]


@pytest.mark.skip('only doc484 docstrings are supported')
def test_transform_yields_tuple():
    """Test output produced when using named values in a Yields section in
    numpy or google format"""
    assert parse('''
:Yields: * **result1** (*str*) -- Description of first item
         * **result2** (*bool*) -- Description of second item
''') == [
        ('return', 'Iterable[Tuple[str, bool]]')
    ]


@pytest.mark.skip('only doc484 docstrings are supported')
def test_returns_tuple():
    """Test output produced when using named values in a Returns section in
    numpy or google format"""
    assert parse('''
:returns: * **result1** (*str*) -- Description of first item
          * **result2** (*bool*) -- Description of second item
''') == [
        ('return', 'Tuple[str, bool]')
    ]
