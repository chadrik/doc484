import re
import inspect
from collections import OrderedDict

from typing import List, Tuple, Dict, Optional

from sphinx.ext.napoleon.docstring import GoogleDocstring, NumpyDocstring
from sphinx.ext.napoleon import Config

from docutils.core import publish_doctree
from docutils.utils import SystemMessage

from mypy.plugin import Plugin, DocstringParserContext
from mypy.fastparse import parse_type_comment
from mypy.types import Type


def _cleandoc(docstring: str) -> str:
    return inspect.cleandoc(docstring).replace('`', '')


class DocstringFormat:
    name = ''
    sections = None  # type: List[str]

    def __init__(self):
        self._sections = [re.compile(s) for s in self.sections]

    def matches(self, docstring: str) -> bool:
        return any(s.search(docstring) for s in self._sections)

    def parse(self, docstring: str) -> Tuple[Dict[str, str], Optional[str]]:
        raise NotImplementedError

    def do_parse(self, docstring: str) -> Tuple[Dict[str, Optional[str]], Optional[str]]:
        params, result = self.parse(docstring)
        for k, v in params.items():
            if v is not None:
                params[k] = clean(v)
        if result is not None:
            result = clean(result)
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

    def parse(self, docstring: str) -> Tuple[Dict[str, str], Optional[str]]:
        docstring = self.to_rest(docstring)
        params = OrderedDict()
        result = None

        try:
            document = publish_doctree(docstring)
        except SystemMessage:
            return params, result

        dom = document.asdom()
        # print(dom.toprettyxml())
        for field in dom.getElementsByTagName('field'):
            field_name = field.getElementsByTagName('field_name')[0]
            data = field_name.firstChild.data
            parts = data.strip().split()
            if len(parts) == 2:
                kind, name = parts
                if kind == 'type':
                    paragraph = field.getElementsByTagName('paragraph')[0]
                    params[name] = elem_value(paragraph)
                elif name not in params:
                    pass
                    # params[name] = None
            elif len(parts) == 1 and parts[0] == 'rtype':
                paragraph = field.getElementsByTagName('paragraph')[0]
                result = elem_value(paragraph)
            elif len(parts) == 1 and parts[0] == 'Yields':
                # FIXME: we need a way to report a warning
                print("Warning: Yields should be converted to Iterable[]")
                # items = field.getElementsByTagName('list_item')
                # if items:
                #     result = _named_items(items)
                # else:
                #     paragraph = field.getElementsByTagName('paragraph')[0]
                #     result = elem_value(paragraph.getElementsByTagName('emphasis')[0])
                # result = 'Iterable[' + result + ']'
            elif len(parts) == 1 and parts[0] == 'returns':
                items = field.getElementsByTagName('list_item')
                if items:
                    result = _named_items(items)

        return params, result


class RestFormat(RestBaseFormat):
    name = 'rest'
    sections = [
        r'(\n|^):param ',
        r'(\n|^):rtype:',
        r'(\n|^):Yields:'
    ]

    def to_rest(self, docstring: str) -> str:
        return _cleandoc(docstring)


class NumpyFormat(RestBaseFormat):
    name = 'numpy'
    sections = [
        r'(\n|^)Parameters\n----------\n',
        r'(\n|^)Returns\n-------\n',
        r'(\n|^)Yields\n------\n'
    ]

    def to_rest(self, docstring: str) -> str:
        return str(NumpyDocstring(_cleandoc(docstring), self.config))


class GoogleFormat(RestBaseFormat):
    name = 'google'
    sections = [
        r'(\n|^)Args:\n',
        r'(\n|^)Returns:\n',
        r'(\n|^)Yields:\n'
    ]

    def to_rest(self, docstring: str) -> str:
        return str(GoogleDocstring(_cleandoc(docstring), self.config))


default_format = RestFormat()
formats = [NumpyFormat(), GoogleFormat(), default_format]
format_map = {f.name: f for f in formats}


# Conversions
# -----------

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


def clean(s):
    return s.strip().replace('\n', ' ')


# FIXME: no longer used.
# we can't add types from docstring without also inserting the import statements
def standardize_docstring_type(s: str, is_result=False) -> str:
    processed = []
    s = clean(s)

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


# def convert_docstring_type(s: Optional[str], line: int) -> Type:
#     if s is None:
#         return AnyType()
#     s = standardize_docstring_type(s)
#     try:
#         return parse_str_as_type(s, line)
#     except TypeParseError:
#         print("failed to parse: %r" % s)
#         return AnyType()


def guess_format(docstring: str) -> DocstringFormat:
    """
    Convert the passed docstring to reStructuredText format.

    Parameters
    ----------
    docstring : str
        the docstring to convert

    Returns
    -------
    DocstringFormat
    """
    docstring = inspect.cleandoc(docstring)
    for format in formats:
        if format.matches(docstring):
            return format
    return default_format


def elem_value(node):
    # print(type(node))
    if hasattr(node, 'data'):
        return node.data
    else:
        return ''.join([elem_value(x) for x in node.childNodes])


def _named_items(items):
    results = []
    for item in items:
        paragraph = item.getElementsByTagName('paragraph')[0]
        results.append(elem_value(
            paragraph.getElementsByTagName('emphasis')[0]))
    if len(results) > 1:
        return 'Tuple[' + ', '.join(results) + ']'
    else:
        return results[0]


# def parse_docstring2(docstring: str, line: int) -> Dict[str, Type]:
#     docstring = to_rest(docstring)
#     params, result = parse_rest(docstring)
#     arg_types = {k: convert_docstring_type(v, line)
#                  for k, v in params.items() if v is not None}
#     if result is not None:
#         arg_types['return'] = convert_docstring_type(result, line)
#     return arg_types


def _parse_docstring(docstring: str, default_format='auto'
                     ) -> Tuple[Dict[str, str], Optional[str]]:
    if default_format == 'auto':
        format = guess_format(docstring)
    else:
        format = format_map[default_format]
    # print(repr(inspect.cleandoc(docstring)))
    # print("guessed %s" % format.name)
    return format.do_parse(docstring)


def parse_docstring(ctx: DocstringParserContext) -> Dict[str, Type]:
    # default_return_type = opts.get('default_return_type', None)
    # format_str = opts.get('format', 'auto')
    default_return_type = None  # type: Optional[str]
    format_str = 'auto'
    params, result = _parse_docstring(ctx.docstring, format_str)
    arg_types = {k: parse_type_comment(v, ctx.line, ctx.errors)
                 for k, v in params.items() if v is not None}
    if result is not None:
        arg_types['return'] = parse_type_comment(result, ctx.line, ctx.errors)
    elif ctx.docstring and default_return_type:
        arg_types['return'] = parse_type_comment(default_return_type, ctx.line, ctx.errors)
    return arg_types


class MypydocPlugin(Plugin):
    def get_docstring_parser_hook(self):
        return parse_docstring


def plugin(version):
    return MypydocPlugin


if __name__ == '__main__':
    from mypy.main import main
    import mypy.hooks
    mypy.hooks.docstring_parser = parse_docstring
    main(None)
