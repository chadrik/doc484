from mypydoc import parse_rest, to_rest, standardize_docstring_type

from typing import List


class CustomType(object):
    pass


def parse(docstring):
    params, result = parse_rest(docstring)
    return ([(k, standardize_docstring_type(v)) for k, v in params.items()],
            standardize_docstring_type(result))


def test_basic():
    assert parse('''
:param path: The path of the :obj:`file` to wrap
:type path: str
:param basic_type: basic type description
:type basic_type: bool''')[0] == [
        ('path', 'str'),
        ('basic_type', 'bool')
    ]


def test_pep484():
    assert parse('''
:param pep484_type: valid pep484 type description
:type pep484_type: Union[Dict[str, int], str]
:param multiline_pep484_type: pep484 type description spanning multiple lines
:type multiline_pep484_type: Union[Dict[str,int],
    List[Tuple[str, int]]]''')[0] == [
        ('pep484_type', 'Union[Dict[str, int], str]'),
        ('multiline_pep484_type', 'Union[Dict[str,int], List[Tuple[str, int]]]')
    ]


def test_custom_type():
    assert parse('''
:param custom_type: The :class:`CustomType` instance to wrap
:type custom_type: CustomType''')[0] == [
        ('custom_type', 'CustomType')
    ]


def test_transform_union():
    assert parse('''
:param union_or: type union using 'or'
:type union_or: int or float or str
:param union_pipe: type union using '|'
:type union_pipe: int | float|str''')[0] == [
        ('union_or', 'Union[int, float, str]'),
        ('union_pipe', 'Union[int, float, str]'),
    ]


def test_transform_lower_dict():
    assert parse('''
:param lower_dict: lower-case dict (pycharm style)
:type lower_dict: dict[str, int]''')[0] == [
        ('lower_dict', 'Dict[str, int]'),
    ]


def test_transform_optional():
    assert parse('''
:param optional: optional parameter
:type optional: str or int, optional''')[0] == [
        ('optional', 'Optional[Union[str, int]]'),
    ]


def test_missing():
    assert parse('''
:param missing_type: parameter that has no type pair
:type  missing_param: bool''')[0] == [
        ('missing_type', 'Any'),  # FIXME: might be best to exclude this and rely on update_signature
        ('missing_param', 'bool'),
    ]


def test_returns():
    assert parse('''
:returns: simple return value
:rtype: bool''')[1] == 'bool'


def test_yields_with_description():
    """Test output produced when using Yields in numpy or google format
    """
    assert parse('''
:Yields: *bool* -- Description of return value.''')[1] == 'Iterable[bool]'


def test_yields_without_description():
    """Test output produced when using Yields in numpy or google format
    """
    assert parse('''
:Yields: *bool*''')[1] == 'Iterable[bool]'


def test_yields_tuple():
    """Test output produced when using named values in a Yields section in
    numpy or google format"""
    assert parse('''
:Yields: * **result1** (*str*) -- Description of first item
         * **result2** (*bool*) -- Description of second item
''')[1] == 'Iterable[Tuple[str, bool]]'


def test_returns_tuple():
    """Test output produced when using named values in a Returns section in
    numpy or google format"""
    assert parse('''
:returns: * **result1** (*str*) -- Description of first item
          * **result2** (*bool*) -- Description of second item
''')[1] == 'Tuple[str, bool]'


def test_numpydoc():
    assert to_rest('''
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
    ''') == '''
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
    assert to_rest('''
        Yields
        ------
        str
            Description of return value.
    ''') == '''
:Yields: *str* -- Description of return value.
'''


def test_numpydoc_tuple_result():
    assert to_rest('''
        Returns
        -------
        result1: str
            Description of first item
        result2: bool
            Description of second item
    ''') == '''
:returns: * **result1** (*str*) -- Description of first item
          * **result2** (*bool*) -- Description of second item
'''


def test_numpydoc_named_result():
    assert to_rest('''
        Returns
        -------
        result1: str
            Description of first item
    ''') == '''
:returns: **result1** -- Description of first item
:rtype: str
'''

    # print(NumpyDocstring(docstring))
# :returns: A buffered writable file descriptor
# :rtype: BufferedFileStorage


def myfunc_test1(arg1,
          arg2,
          arg3=True,
          arg4='string',
          arg5=None  # type: List[str]
          ):
    pass


def myfunc_test2(arg1,
          arg2,
          arg3=True,
          arg4='string',
          arg5: List[str] = None
          ):
    pass


def myfunc_test3(arg1,
          arg2,
          arg3=True,
          arg4='string',
          arg5=None
          ):
    """
    :param arg1:
    :param arg2:
    :param arg3:
    :param arg4:
    :param arg5:
    :type arg5: tuple[str]
    """
    pass
