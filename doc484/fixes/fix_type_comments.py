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
import re
from lib2to3 import pytree
from lib2to3.pgen2 import token
from lib2to3 import fixer_base
from lib2to3.fixer_util import syms
from lib2to3.pygram import python_grammar

from ..formats import parse_docstring

number2symbol = python_grammar.number2symbol
TYPE_REG = re.compile('\s*#\s*type:.*')


def _get_type(typ, default='Any'):
    return default if typ is None else typ.type


def is_type_comment(comment):
    return TYPE_REG.match(comment)


def find_classdef(node):
    while True:
        parent = node.parent
        if parent is None:
            return None
        elif parent.type == syms.classdef:
            return parent
        node = parent


def get_docstring(stmt):
    if isinstance(stmt, pytree.Node) and \
           stmt.children[0].type == token.STRING:
        doc = stmt.children[0].value
        # FIXME: something better than eval
        return eval(doc), stmt.children[0].lineno
    else:
        return None, None


def keep_arg(i, arg_name, typ):
    # we can't *easily* tell from here if the current func is a
    # method, but the below is a pretty good assurance that we can skip
    # the current arg.
    # there is nothing wrong with including self or cls, but pep484
    # supports omitting it for brevity.
    return not (i == 0 and arg_name in {'self', 'cls'} and typ is None)


class FixTypeComments(fixer_base.BaseFix):
    run_order = 4 #use a lower order since lambda is part of other
                  #patterns
    BM_compatible = True

    PATTERN = """ 
    funcdef< 'def' name=any parameters< '(' [args=any] ')' >
           ['->' any] ':' suite=any+ >
    """

    def transform(self, node, results):
        suite = results["suite"]
        args = results.get("args")
        name = results["name"]
        classdef = find_classdef(name)
        is_method = classdef is not None
        # print name, is_method

        if suite[0].children[1].type == token.INDENT:
            indent_node = suite[0].children[1]
            doc_node = suite[0].children[2]
        else:
            # e.g. "def foo(...): x = 5; y = 7"
            return

        docstring, line = get_docstring(doc_node)
        if docstring is None:
            return

        comment = indent_node.prefix

        types = []  # type: List[str]
        params, result = parse_docstring(docstring, line=line,
                                         filename=self.filename)
        if args:
            # if args.type == syms.tfpdef:
            #     pass
            if args.type == syms.typedargslist:
                arg_list = []
                consume = True
                for arg in args.children:
                    if consume and arg.type == token.NAME:
                        arg_list.append(arg)
                        consume = False
                    elif arg.type == token.COMMA:
                        consume = True
            elif args.type == token.NAME:
                arg_list = [args]
            else:
                raise TypeError(args)

            for i, arg in enumerate(arg_list):
                typ = params.get(arg.value)
                if not is_method or keep_arg(i, arg.value, typ):
                    types.append(_get_type(typ))

        if result is None and all([x == 'Any' for x in types]):
            # no effect: don't bother with type comment
            return

        default_return = 'None'
        typestr = '# type: (%s) -> %s\n' % (', '.join(types),
                                            _get_type(result, default_return))

        if comment and not is_type_comment(comment):
            # push existing non-type comment to next line
            typestr += comment

        indent_node.prefix = indent_node.value + typestr
        suite[0].changed()
