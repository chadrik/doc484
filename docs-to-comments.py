from __future__ import absolute_import, print_function
from redbaron import RedBaron
import sys
import re
import os
import os.path
import argparse
import doc484


TYPE_REG = re.compile('\s*#\s*type:.*')


def _get_type(typ):
    return 'Any' if typ is None else typ.type


def convert_file(path, dry_run=False):
    print(path)
    with open(path, 'r') as f:
        red = RedBaron(f.read())
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
            params, result = doc484.parse_docstring(s)
            if obj.arguments:
                for i, arg in enumerate(obj.arguments):
                    typ = params.get(arg.name.value)
                    # we can't *easily* tell from here if the current func is a
                    # method, but the below is a pretty good assurance that we can skip
                    # the arg
                    if i == 0 and arg.name.value in {'self', 'cls'} and typ is None:
                        continue
                    types.append(_get_type(typ))

            typestr = '# type: (%s) -> %s' % (', '.join(types), _get_type(result))
            if type_comment is not None and TYPE_REG.match(type_comment.value):
                type_comment.value = typestr
            else:
                obj.insert(0, typestr)
    if dry_run:
        print(red.dumps())
    else:
        with open(path, 'w') as f:
            f.write(red.dumps())


def convert(path, dry_run=False):
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if name.endswith('.py'):
                    fullpath = os.path.join(root, name)
                    convert_file(fullpath, dry_run=dry_run)
    else:
        convert_file(path, dry_run=dry_run)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Path to convert")
    args = parser.parse_args()
    convert(args.path)
