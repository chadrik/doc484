from __future__ import absolute_import, print_function

import docutils.nodes
from docutils.core import Publisher
from docutils import io
from docutils.utils import SystemMessage
from docutils.nodes import Element
from docutils.readers.standalone import Reader as _Reader

from doc484.parsers import Arg

if False:
    from typing import *


def _clean_type(s):
    return s.strip().replace('\n', ' ')


class Reader(_Reader):
    doc_logger = None

    def pass_to_format_logger(self, msg):
        if msg['type'] == 'ERROR':
            log = self.doc_logger.error
        elif msg['type'] == 'WARNING':
            log = self.doc_logger.warning
        else:
            return
        log(Element.astext(msg), line=msg['line'])

    def new_document(self):
        document = _Reader.new_document(self)
        document.reporter.stream = False
        document.reporter.attach_observer(self.pass_to_format_logger)
        return document


def publish_doctree(source, logger):
    # type: (str, Any) -> docutils.nodes.Node
    pub = Publisher(reader=None, parser=None, writer=None,
                    settings=None,
                    source_class=io.StringInput,
                    destination_class=io.NullOutput)
    pub.reader = Reader(None, 'restructuredtext')
    pub.reader.doc_logger = logger
    pub.set_writer('null')
    pub.parser = pub.reader.parser
    pub.process_programmatic_settings(None, None, None)
    pub.set_source(source, None)
    pub.set_destination(None, None)
    output = pub.publish(enable_exit_status=False)
    return pub.document


class RestDocstring(object):

    def __init__(self, docstring, logger):
        self.docstring = docstring
        self.logger = logger

    def parse(self):
        params = []
        returns = None
        yields = None

        try:
            document = publish_doctree(self.docstring, self.logger)
        except SystemMessage:
            return params, returns, yields

        for field in document.traverse(condition=docutils.nodes.field):
            field_name = field.traverse(condition=docutils.nodes.field_name)[0]
            data = field_name.astext()
            # data is e.g.  'type foo'
            parts = data.strip().split()
            if len(parts) == 1 and parts[0] == 'returns':
                # converted google/numpy format with named results:
                # * **result1** (*str*) -- Description of first item
                # * **result2** (*bool*)
                # * **result3** (*int*) -- Description of third item
                # * *other stuff that is not return value.*
                items = field.traverse(condition=docutils.nodes.list_item)
                if items:
                    assert returns is None
                    item_types = []  # type: List[str]
                    for item in items:
                        text = item.astext()
                        item_types.append(Arg(text, field.line))
                        returns = item_types

            elif len(parts) == 1 or (len(parts) == 2 and parts[0] == 'type'):
                paras = field.traverse(condition=docutils.nodes.paragraph)
                if not paras:
                    continue
                paragraph = paras[0]
                arg = Arg(_clean_type(paragraph.astext()), paragraph.line)
                if len(parts) == 2:
                    # e.g. :type foo: xxxx
                    kind, name = parts
                    params.append((name, arg))
                elif len(parts) == 1 and parts[0] == 'rtype':
                    # e.g. :rtype: xxxx
                    assert returns is None
                    returns = [arg]
                elif len(parts) == 1 and parts[0] == 'Yields':
                    # e.g. converted from numpy/google format
                    assert yields is None
                    yields = [arg]

        return params, returns, yields