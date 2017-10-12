from __future__ import absolute_import, print_function
import re


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


def standardize_docstring_type(s, is_result=False):
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
