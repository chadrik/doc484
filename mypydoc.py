import re
import inspect
from collections import OrderedDict

from typing import List, Tuple, Dict, NamedTuple, Optional, TYPE_CHECKING, Type as Class

from sphinx.ext.napoleon.docstring import GoogleDocstring, NumpyDocstring
from sphinx.ext.napoleon import Config

import docutils.nodes
from docutils.core import publish_doctree
from docutils.utils import SystemMessage

from mypy.plugin import Plugin, DocstringParserContext
from mypy.errors import Errors
from mypy.fastparse import parse_type_comment
from mypy.types import Type


YIELDS_ERROR = "'Yields' is not supported. Use 'Returns' with Iterator[]"
NAMED_ITEMS_ERROR = 'Named results are not supported. Use Tuple[] or NamedTuple'


Arg = NamedTuple('Arg', [
    ('type', str),
    ('line', int),
])


def _cleandoc(docstring: str) -> str:
    return inspect.cleandoc(docstring).replace('`', '')


def _clean_type(s):
    return s.strip().replace('\n', ' ')


def compile(*regexs):
    return [re.compile(s) for s in regexs]


class DocstringFormat:
    name = ''
    sections = None  # type: List[str]

    def __init__(self, line: int, errors: Errors):
        self.errors = errors
        self.line = line

    def warning(self, message: str, line: int):
        self.errors.report(line + self.line, 0, message=message, severity='waring')

    def error(self, message: str, line: int):
        self.errors.report(line + self.line, 0, message=message, severity='error')

    @classmethod
    def matches(cls, docstring: str) -> bool:
        return any(s.search(docstring) for s in cls.sections)

    def parse(self, docstring: str) -> Tuple[Dict[str, str], Optional[Arg]]:
        raise NotImplementedError

    def do_parse(self, docstring: str) -> Tuple[Dict[str, Optional[str]], Optional[str]]:
        params, result = self.parse(docstring)
        # for k, v in params.items():
        #     if v is not None:
        #         params[k] = _clean_type(v)
        # if result is not None:
        #     result = _clean_type(result)
        return params, result


class RestBaseFormat(DocstringFormat):
    """
    Base class for all types that convert to restructuredText as a common parsing format
    """
    config = Config(napoleon_use_param=True, napoleon_use_rtype=True)

    def to_rest(self, docstring: str) -> str:
        """
        Convert a docstring from the native format to rest
        """
        raise NotImplementedError

    def _named_items_to_tuple(self, items, line):
        results = []
        for item in items:
            paragraph = item.traverse(condition=docutils.nodes.paragraph)[0]
            results.append(
                Arg(_clean_type(paragraph.traverse(condition=docutils.nodes.emphasis)[0].astext()),
                    paragraph.line))
        if len(results) > 1:
            # return 'Tuple[' + ', '.join(results) + ']'
            self.warning(NAMED_ITEMS_ERROR, line)
        else:
            return results[0]

    def parse(self, docstring: str) -> Tuple[Dict[str, str], Optional[Arg]]:
        docstring = self.to_rest(docstring)
        params = OrderedDict()
        result = None  # type: Arg

        try:
            document = publish_doctree(docstring)
        except SystemMessage:
            return params, result

        for field in document.traverse(condition=docutils.nodes.field):
            field_name = field.traverse(condition=docutils.nodes.field_name)[0]
            data = field_name.astext()
            # data is e.g.  'type foo'
            parts = data.strip().split()
            if len(parts) == 1 and parts[0] == 'returns':
                items = field.traverse(condition=docutils.nodes.list_item)
                if items:
                    # special case to print warning for named return values
                    # tmp = self._named_items_to_tuple(items, field.line)
                    # assert tmp is None
                    self.warning(NAMED_ITEMS_ERROR, field.line)
            elif len(parts) in (1, 2):
                print(parts)
                paragraph = field.traverse(condition=docutils.nodes.paragraph)[0]
                arg = Arg(_clean_type(paragraph.astext()), paragraph.line)
                if len(parts) == 2:
                    # e.g. type foo: xxxx
                    kind, name = parts
                    if kind == 'type':
                        params[name] = arg
                        # elif name not in params:
                        #     params[name] = None
                elif len(parts) == 1 and parts[0] == 'rtype':
                    # e.g. rtype: xxxx
                    print(arg)
                    result = arg
                elif len(parts) == 1 and parts[0] == 'Yields':
                    paragraph = field.traverse(condition=docutils.nodes.paragraph)[0]
                    self.warning(YIELDS_ERROR, paragraph.line)
                    # items = field.getElementsByTagName('list_item')
                    # if items:
                    #     result = _named_items_to_tuple(items)
                    # else:
                    #     paragraph = field.getElementsByTagName('paragraph')[0]
                    #     result = _elem_value(paragraph.getElementsByTagName('emphasis')[0])
                    # result = 'Iterator[' + result + ']'

        return params, result


class RestFormat(RestBaseFormat):
    name = 'rest'
    sections = compile(
        r'(\n|^):param ',
        r'(\n|^):rtype:',
        r'(\n|^):Yields:'
    )

    def to_rest(self, docstring: str) -> str:
        return _cleandoc(docstring)


class NumpyFormat(RestBaseFormat):
    name = 'numpy'
    sections = compile(
        r'(\n|^)Parameters\n----------\n',
        r'(\n|^)Returns\n-------\n',
        r'(\n|^)Yields\n------\n'
    )

    def to_rest(self, docstring: str) -> str:
        return str(NumpyDocstring(_cleandoc(docstring), self.config))


class GoogleFormat(RestBaseFormat):
    name = 'google'
    sections = compile(
        r'(\n|^)Args:\n',
        r'(\n|^)Returns:\n',
        r'(\n|^)Yields:\n'
    )

    def to_rest(self, docstring: str) -> str:
        return str(GoogleDocstring(_cleandoc(docstring), self.config))


default_format = RestFormat
formats = [NumpyFormat, GoogleFormat, default_format]  # type: List[DocstringFormat]
format_map = {f.name: f for f in formats}  # type: Dict[str, DocstringFormat]


# Transformations
# ---------------

# FIXME: currently, if these replacements are successful, it will result in an
# error because the corresponding type is not imported within the module.
# e.g. error: Name 'Sequence' is not defined
translations = {
    'boolean': 'bool',
    'string': 'str',
    'integer': 'int',
    'list': 'List',
    'dict': 'Dict',
    'dictionary': 'Dict',
    # types below need to be imported from typing into the module being parsed:
    'any': 'Any',
    'tuple': 'Tuple',
    'set': 'Set',
    'sequence': 'Sequence',
    'iterable': 'Iterable',
    'mapping': 'Mapping',
}

# known_generic_types = [
#     'List', 'Set', 'Dict', 'Iterable', 'Sequence', 'Mapping',
# ]
#
# # Some natural language patterns that we want to support in hooks.
# known_patterns = [
#     ('list of ?', 'List[?]'),
#     ('set of ?', 'List[?]'),
#     ('sequence of ?', 'Sequence[?]'),
# ]

union_regex = re.compile(r'(?:\s+or\s+)|(?:\s*\|\s*)')

optional_regex = re.compile(r'(.*)(,\s*optional\s*$)')


def standardize_docstring_type(s: str, is_result=False) -> str:
    processed = []
    s = _clean_type(s)

    if is_result:
        optional = False
    else:
        # optional
        optional = optional_regex.search(s)
        if optional:
            s = optional.group(1)

    parts = union_regex.split(s)
    for type_str in parts:
        for find, replace in translations.items():
            type_str = re.sub(r'\b' + find + r'\b', replace, type_str)
        processed.append(type_str)
    if len(processed) > 1:
        s = 'Union[' + ', '.join(processed) + ']'
    else:
        s = processed[0]

    if optional:
        s = 'Optional[' + s + ']'
    return s

# ----


def guess_format(docstring: str) -> DocstringFormat:
    """
    Convert the passed docstring to reStructuredText format.

    Parameters
    ----------
    docstring : str
        the docstring to convert

    Returns
    -------
    Class[DocstringFormat]
    """
    docstring = inspect.cleandoc(docstring)
    for format in formats:
        if format.matches(docstring):
            return format
    return default_format


def _parse_docstring(docstring: str, line: int=0, errors: Optional[Errors]=None,
                     default_format='auto'
                     ) -> Tuple[Dict[str, str], Optional[Arg]]:
    if default_format == 'auto':
        format = guess_format(docstring)
    else:
        format = format_map[default_format]
    if errors is None:
        errors = Errors()
    return format(line, errors).do_parse(docstring)


# Entry Points
# ------------

def parse_docstring(ctx: DocstringParserContext) -> Dict[str, Type]:
    # default_return_type = opts.get('default_return_type', None)
    # format_str = opts.get('format', 'auto')
    default_return_type = None  # type: Optional[str]
    format_str = 'auto'
    params, result = _parse_docstring(ctx.docstring, ctx.line, ctx.errors, format_str)
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
