import re
from collections import OrderedDict

from typing import List, Tuple, Dict
import mypy.parse
import mypy.types
from mypy import nodes

from mypy.types import Type, CallableType, AnyType
from mypy.parsetype import parse_str_as_type, TypeParseError, parse_str_as_signature

from sphinx.ext.napoleon.docstring import GoogleDocstring, NumpyDocstring
from sphinx.ext.napoleon import Config
config = Config(napoleon_use_param=True, napoleon_use_rtype=True)

from docutils.core import publish_doctree, publish_string
from docutils.utils import SystemMessage


rest_sections = [
    '\n:param ',
    '\n:rtype:',
    '\n:Yields:'
]

numpy_sections = [
    '\nParameters\n----------\n',
    '\nReturns\n-------\n',
    '\nYields\n------\n'
]

google_sections = [
    '\nArgs:\n',
    '\nReturns:\n',
    '\nYields:\n'
]

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
# # Some natural language patterns that we want to support in docstrings.
# known_patterns = [
#     ('list of ?', 'List[?]'),
#     ('set of ?', 'List[?]'),
#     ('sequence of ?', 'Sequence[?]'),
# ]

union_regex = re.compile(r'(?:\s+or\s+)|(?:\s*\|\s*)')

optional_regex = re.compile(r'(.*)(,\s*optional\s*$)')


def clean(s):
    return s.strip().replace('\n', ' ')


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


def convert_docstring_type(s: str, line: int) -> Type:
    s = standardize_docstring_type(s)
    try:
        return parse_str_as_type(s, line)
    except TypeParseError:
        print("failed to parse: %r" % s)
        return AnyType()
    # try:
    #     return parse_str_as_type(standardize_docstring_type(s), line)
    # except TypeParseError:
    #     return AnyType()


def to_rest(docstring):
    """
    Convert the passed docstring to reStructuredText format.

    Parameters
    ----------
    docstring : str
        the docstring to convert

    Returns
    -------
    str
    """
    docstring = docstring.replace('`', '')
    for rest, numpy, google in zip(rest_sections, numpy_sections,
                                   google_sections):
        if rest in docstring:
            return docstring
        if numpy in docstring:
            print("Using numpy format")
            return str(NumpyDocstring(docstring, config))
        if google in docstring:
            print("Using google format")
            return str(GoogleDocstring(docstring, config))
    print("Unknown format")
    return docstring


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


def parse_rest(docstring: str) -> Tuple[Dict[str, str], str]:
    params = OrderedDict()
    result = 'Any'

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
                params[name] = 'Any'
        elif len(parts) == 1 and parts[0] == 'rtype':
            paragraph = field.getElementsByTagName('paragraph')[0]
            result = elem_value(paragraph)
        elif len(parts) == 1 and parts[0] == 'Yields':
            items = field.getElementsByTagName('list_item')
            if items:
                result = _named_items(items)
            else:
                paragraph = field.getElementsByTagName('paragraph')[0]
                result = elem_value(paragraph.getElementsByTagName('emphasis')[0])
            result = 'Iterable[' + result + ']'
        elif len(parts) == 1 and parts[0] == 'returns':
            items = field.getElementsByTagName('list_item')
            if items:
                result = _named_items(items)

    return params, result


def parse_docstring(docstring: str, line: int) -> CallableType:
    docstring = to_rest(docstring)
    # print(docstring)
    params, result = parse_rest(docstring)
    return to_callable(params, result, line)


def parse_docstring2(docstring: str, line: int) -> Tuple[Dict[str, Type], Type]:
    docstring = to_rest(docstring)
    params, result = parse_rest(docstring)
    arg_types = {k: convert_docstring_type(v, line) for k, v in params.items()}
    return_type = convert_docstring_type(result, line)
    return arg_types, return_type


def to_callable(params, result, line: int) -> CallableType:
    arg_types = []
    arg_kinds = []
    arg_names = []
    for name, type_str in params.items():
        if name.startswith('**'):
            kind = nodes.ARG_STAR2
            name = name[2:]
        if name.startswith('*'):
            kind = nodes.ARG_STAR
            name = name[1:]
        else:
            kind = nodes.ARG_POS

        arg = convert_docstring_type(type_str, line)
        # print(x.toprettyxml())
        # print(name)
        # print('%s --> %s' % (type_str, arg))
        arg_types.append(arg)
        arg_kinds.append(kind)
        arg_names.append(name)

    ret_type = convert_docstring_type(result, line)

    return CallableType(arg_types,
                        arg_kinds,
                        arg_names,
                        ret_type, None,
                        is_ellipsis_args=False)


class DocParser(mypy.parse.Parser):
    def parse_docstring(self, docstring: str, line: int) -> CallableType:
        return parse_docstring(docstring, line)

    # overrides that supports sparse updates
    def update_signature(self, func_name: str, is_method: bool,
                         args: List[nodes.Argument], sig: CallableType,
                         line: int, column: int) -> CallableType:
        # sig is either parsed from 'type' comments or docstrings

        # NOTE:
        # Multi-line comment annotations currently only work when using the
        # --fast-parser command line option. This is not enabled by default
        # because the option isn’t supported on Windows yet
        if is_method:
            fargs = args[1:]
        else:
            fargs = args
        # parsed from function def:
        arg_kinds = [arg.kind for arg in fargs]
        arg_types = [arg.variable.type for arg in fargs]
        arg_names = [arg.variable.name() for arg in fargs]

        print("real types: %s" % arg_types)
        print("doc types:  %s" % sig.arg_types)
        print("real kinds: %s" % arg_kinds)
        print("doc kinds:  %s" % sig.arg_kinds)
        print("real names: %s" % arg_names)
        print("doc names:  %s" % sig.arg_names)
        print("-" * 40)
        # if all(sig.arg_names) and arg_names:
        #     # fill in missing arguments
        #     override_kinds = dict(zip(sig.arg_names, sig.arg_kinds))
        #     override_types = dict(zip(sig.arg_names, sig.arg_types))
        #     # print("Overrides")
        #     # for name, typ in zip(sig.arg_names, sig.arg_types):
        #     #     print("   %s: %s" % (name, typ))
        #
        #     sig.arg_kinds = [override_kinds.get(name, kind)
        #                      for name, kind in zip(arg_names, arg_kinds)]
        #     sig.arg_types = [override_types.get(name, typ)
        #                      for name, typ in zip(arg_names, arg_types)]

        for name, real_kind, real_type, merged_kind, merged_type in zip(
                arg_names, arg_kinds, arg_types, sig.arg_kinds, sig.arg_types):
            print(name)
            print("  kind: %s --> %s" % (real_kind, merged_kind))
            print("  type: %s --> %s" % (real_type, merged_type))
        print("=" * 40)
        return super(DocParser, self).update_signature(func_name, is_method, args,
                                                       sig, line, column)
        #
        # if sig.is_ellipsis_args:
        #     # When we encounter an ellipsis, fill in the arg_types with
        #     # a bunch of AnyTypes, emulating Callable[..., T]
        #     arg_types = [AnyType()] * len(arg_kinds)  # type: List[Type]
        #     return CallableType(
        #         arg_types,
        #         arg_kinds,
        #         arg_names,
        #         sig.ret_type,
        #         None,
        #         line=line,
        #         column=column)
        # elif is_method and len(sig.arg_kinds) < len(arg_kinds):
        #     self.check_argument_kinds(arg_kinds,
        #                               [nodes.ARG_POS] + sig.arg_kinds,
        #                               line, column)
        #     # Add implicit 'self' argument to signature.
        #     first_arg = [AnyType()]  # type: List[Type]
        #     return CallableType(
        #         first_arg + sig.arg_types,
        #         arg_kinds,
        #         arg_names,
        #         sig.ret_type,
        #         None,
        #         line=line,
        #         column=column)
        # else:
        #     self.check_argument_kinds(arg_kinds, sig.arg_kinds, line, column)
        #     return CallableType(
        #         sig.arg_types,
        #         arg_kinds,
        #         arg_names,
        #         sig.ret_type,
        #         None,
        #         line=line,
        #         column=column)

# mypy.parse.Parser = DocParser

import mypy.docstrings
mypy.docstrings.parse_docstring = parse_docstring2

if __name__ == '__main__':
    from mypy.main import main
    main(None)
