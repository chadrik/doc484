"""Fixer for function definitions with tuple parameters.

def func(((a, b), c), d):
    ...

    ->

def func(x, d):
    ((a, b), c) = x
    ...

It will also support lambdas:

    lambda (x, y): x + y -> lambda t: t[0] + t[1]

    # The parens are a syntax error in Python 3
    lambda (x): x + y -> lambda x: x + y
"""
from __future__ import absolute_import, print_function

import re
from lib2to3 import pytree
from lib2to3.pgen2 import token
from lib2to3 import fixer_base
from lib2to3.fixer_util import syms
from lib2to3.pygram import python_grammar

import doc484.formats as formats

if False:
    from typing import *

number2symbol = python_grammar.number2symbol
TYPE_REG = re.compile('\s*#\s*type:.*')

SPECIAL_METHOD_RETURN = {
    '__init__': 'None'
}


def _get_type(typ, default='Any'):
    return default if typ is None else typ


def is_type_comment(comment):
    return TYPE_REG.match(comment)


def find_classdef(node):
    while True:
        parent = node.parent
        if parent is None:
            return None
        elif parent.type == syms.classdef:
            # return the suite as list
            for child in parent.children:
                if child.type == syms.suite:
                    return [child]
            else:
                raise RuntimeError("could not find suite")
        node = parent


def get_docstring(suite):
    assert isinstance(suite, list)
    if suite[0].children[1].type == token.INDENT:
        indent_node = suite[0].children[1]
        doc_node = suite[0].children[2]
    else:
        # e.g. "def foo(...): x = 5; y = 7"
        return None, None, None

    if isinstance(doc_node, pytree.Node) and \
            doc_node.children[0].type == token.STRING:
        doc = doc_node.children[0].value
        # convert '"docstring"' to 'docstring'
        # FIXME: something better than eval
        return eval(doc), doc_node.children[0].lineno, indent_node
    else:
        return None, None, indent_node


def keep_arg(i, arg_name, typ):
    # we can't *easily* tell from here if the current func is a
    # method, but the below is a pretty good assurance that we can skip
    # the current arg.
    # there is nothing wrong with including self or cls, but pep484
    # supports omitting it for brevity.
    return not (i == 0 and arg_name in {'self', 'cls'} and typ is None)


class FixTypeComments(fixer_base.BaseFix):
    run_order = 4  # use a lower order since lambda is part of other patterns
    BM_compatible = True

    PATTERN = """ 
    funcdef< 'def' name=any parameters< '(' [args=any] ')' >
           ['->' any] ':' suite=any+ >
    """

    def parse_docstring(self, docstring, line):
        if docstring:
            params, result = formats.parse_docstring(docstring, line=line,
                                                     filename=self.filename)
            return {k: v.type for k, v in params.items()}, \
                   result.type if result else None
        else:
            return {}, None

    def transform(self, node, results):
        suite = results["suite"]
        args = results.get("args")
        name_node = results["name"]
        # strip because name_node includes the whitespace prefix.  e.g. ' foo'
        name = str(name_node).strip()
        class_suite = find_classdef(name_node)
        is_method = class_suite is not None

        docstring, line, indent_node = get_docstring(suite)

        comment = indent_node.prefix
        if comment.strip() == '# notype':
            return

        if docstring is None and name == '__init__' and class_suite is not None:
            # fall back to the class docstring
            docstring, line, _ = get_docstring(class_suite)

        has_type_comment = is_type_comment(comment)

        # if we have a default argument map and there's no existing type comment
        # then we can still proceed.
        if docstring is None and not (formats.default_arg_types
                                      and not has_type_comment):
            return

        types = []  # type: List[str]
        params, result = self.parse_docstring(docstring, line)
        if args:
            # if args.type == syms.tfpdef:
            #     pass
            if args.type == syms.typedargslist:
                arg_list = []
                kind_list = []
                consume = True
                kind = ''
                for arg in args.children:
                    if consume and arg.type == token.NAME:
                        arg_list.append(arg)
                        kind_list.append(kind)
                        consume = False
                    elif consume and arg.type == token.STAR:
                        kind = '*'
                    elif consume and arg.type == token.DOUBLESTAR:
                        kind = '**'
                    elif arg.type == token.COMMA:
                        consume = True
                        kind = ''
            elif args.type == token.NAME:
                arg_list = [args]
                kind_list = ['']
            else:
                raise TypeError(args)

            for i, (arg, kind) in enumerate(zip(arg_list, kind_list)):
                typ = params.get(arg.value)
                if typ is None and formats.default_arg_types:
                    typ = formats.default_arg_types.get(arg.value)
                if not is_method or keep_arg(i, arg.value, typ):
                    types.append(kind + _get_type(typ).strip('*'))

        if result is None and all([x.strip('*') == 'Any' for x in types]):
            # no effect: don't bother with type comment
            return

        default_return = formats.default_return_type
        if is_method and name in SPECIAL_METHOD_RETURN:
            default_return = SPECIAL_METHOD_RETURN[name]

        typestr = '# type: (%s) -> %s\n' % (', '.join(types),
                                            _get_type(result, default_return))

        if comment and not has_type_comment:
            # push existing non-type comment to next line
            typestr += comment

        indent_node.prefix = indent_node.value + typestr
        suite[0].changed()
