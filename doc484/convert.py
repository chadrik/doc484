#!/usr/bin/env python
from __future__ import absolute_import, print_function
from redbaron import RedBaron
import sys
import re
import os
import os.path
from .formats import parse_docstring


TYPE_REG = re.compile('\s*#\s*type:.*')


def _get_type(typ, default='Any'):
    return default if typ is None else typ.type


def convert_string(contents, default_return='Any'):
    red = RedBaron(contents)
    for obj in red.find_all('def'):
        doc_node = None
        type_comment = None
        for node in obj.value:
            if node.type == 'endl':
                pass
            elif node.type == 'comment':
                if type_comment is None:
                    # record the first comment.  it may be the type comment
                    type_comment = node
            elif node.type == 'string':
                doc_node = node
                break
            else:
                break
        if doc_node is not None:
            s = doc_node.to_python()
            types = []
            line = doc_node.absolute_bounding_box.top_left.line
            params, result = parse_docstring(s, line=line)
            if obj.arguments:
                for i, arg in enumerate(obj.arguments):
                    typ = params.get(arg.name.value)
                    # we can't *easily* tell from here if the current func is a
                    # method, but the below is a pretty good assurance that we can skip
                    # the current arg.
                    # there is nothing wrong with including self or cls, but pep484
                    # supports omitting it for brevity.
                    if i == 0 and arg.name.value in {'self', 'cls'} and typ is None:
                        continue
                    types.append(_get_type(typ))

            typestr = '# type: (%s) -> %s' % (', '.join(types),
                                              _get_type(result, default_return))
            if type_comment is not None and TYPE_REG.match(type_comment.value):
                type_comment.value = typestr
            else:
                obj.insert(0, typestr)
    return red.dumps()


def convert_file(path, dry_run=False, default_return='Any'):
    print(path)
    with open(path, 'r') as f:
        output = convert_string(f.read(), default_return=default_return)

    if dry_run:
        print(output)
    else:
        with open(path, 'w') as f:
            f.write(output)


def convert(path, dry_run=False, default_return='Any'):
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if name.endswith('.py'):
                    fullpath = os.path.join(root, name)
                    convert_file(fullpath, dry_run=dry_run,
                                 default_return=default_return)
    else:
        convert_file(path, dry_run=dry_run, default_return=default_return)
