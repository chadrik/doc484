from __future__ import absolute_import, print_function

from doc484 import parse_docstring as _parse_docstring

from mypy.plugin import Plugin, DocstringParserContext
from mypy.errors import Errors
from mypy.fastparse import parse_type_comment
from mypy.types import Type

from typing import List, Tuple, Dict, NamedTuple, Optional, TYPE_CHECKING, Type as Class


class Logger:
    def __init__(self, errors):
        self.errors = errors

    def warning(self, message, extra=None):
        self.errors.report(extra['line'], extra['column'], message=message,
                           severity='waring')

    def error(self, message, extra=None):
        self.errors.report(extra['line'], extra['column'], message=message,
                           severity='error')


# Entry Points
# ------------

def parse_docstring(ctx: DocstringParserContext) -> Dict[str, Type]:
    # default_return_type = opts.get('default_return_type', None)
    # format_str = opts.get('format', 'auto')
    default_return_type = None  # type: Optional[str]
    format_str = 'auto'
    params, result = _parse_docstring(ctx.docstring, ctx.line, Logger(ctx.errors),
                                      format_str)
    arg_types = {k: parse_type_comment(v.type, ctx.line + v.line, ctx.errors)
                 for k, v in params.items() if v is not None}
    if result is not None:
        arg_types['return'] = parse_type_comment(result.type, ctx.line + result.line, ctx.errors)
    elif ctx.docstring and default_return_type:
        arg_types['return'] = parse_type_comment(default_return_type, ctx.line, ctx.errors)
    return arg_types


class MypydocPlugin(Plugin):
    def get_docstring_parser_hook(self):
        return parse_docstring


def plugin(version) -> Class[Plugin]:
    return MypydocPlugin


if __name__ == '__main__':
    from mypy.main import main
    import mypy.hooks
    mypy.hooks.docstring_parser = parse_docstring
    main(None)
