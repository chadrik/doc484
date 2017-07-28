from __future__ import absolute_import, print_function

from plugin import parse_docstring, Logger
from doc484 import guess_format

from mypy.errors import Errors
from mypy.plugin import DocstringParserContext
from mypy.types import AnyType


def get_format(docstring):
    format = guess_format(docstring)
    return format(0, Logger(Errors()))


def convert(docstring, line=0):
    ctx = DocstringParserContext(docstring, line, Errors())
    ctx.errors.file = 'dummypath'
    return ctx, parse_docstring(ctx)


def test_invalid_types():
    s = '''
:param union_or: type union using 'or'
:type union_or: int or float or str
:param union_pipe: type union using '|'
:type union_pipe: int | float|str'''
    format = get_format(s)
    ctx, result = convert(s)
    assert ctx.errors.messages() == [
        'dummypath:2: error: invalid type comment or annotation',
        'dummypath:4: error: invalid type comment or annotation'
    ]

    assert list(result.keys()) == ['union_or', 'union_pipe']
    assert isinstance(result['union_or'], AnyType)
    assert isinstance(result['union_pipe'], AnyType)
