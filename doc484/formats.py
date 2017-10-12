import re
import inspect
import logging
from collections import OrderedDict

from typing import List, Tuple, Dict, NamedTuple, Optional, TYPE_CHECKING, Type as Class

import docutils.nodes
from docutils.core import Publisher
from docutils import io
from docutils.utils import SystemMessage
from docutils.nodes import Element
from docutils.readers.standalone import Reader as _Reader
from doc484.parsers import Config, GoogleDocstring, NumpyDocstring

YIELDS_ERROR = "'Yields' is not supported. Use 'Returns' with Iterator[]"
NAMED_ITEMS_ERROR = 'Named results are not supported. Use Tuple[] or NamedTuple'


Arg = NamedTuple('Arg', [
    ('type', str),
    ('line', int),
])

logging.basicConfig(format='%(levelname)-5s: line %(line)s: %(message)s')

_logger = logging.getLogger(__name__)


def _cleandoc(docstring):
    return inspect.cleandoc(docstring).replace('`', '')


def _clean_type(s):
    return s.strip().replace('\n', ' ')


def compile(*regexs):
    return [re.compile(s) for s in regexs]


class Reader(_Reader):
    doc_format = None

    def pass_to_format_logger(self, msg):
        # print(msg.attributes, msg.children)

        if msg['type'] == 'ERROR':
            log = self.doc_format.error
        elif msg['type'] == 'WARNING':
            log = self.doc_format.warning
        else:
            return
        log(Element.astext(msg), line=msg['line'])

    def new_document(self):
        document = _Reader.new_document(self)
        document.reporter.stream = False
        document.reporter.attach_observer(self.pass_to_format_logger)
        return document


def publish_doctree(source, doc_format):
    """
    Set up & run a `Publisher` for programmatic use with string I/O.
    Return the document tree.

    For encoded string input, be sure to set the 'input_encoding' setting to
    the desired encoding.  Set it to 'unicode' for unencoded Unicode string
    input.  Here's one way::

        publish_doctree(..., settings_overrides={'input_encoding': 'unicode'})

    Parameters: see `publish_programmatically`.
    """
    pub = Publisher(reader=None, parser=None, writer=None,
                    settings=None,
                    source_class=io.StringInput,
                    destination_class=io.NullOutput)
    pub.reader = Reader(None, 'restructuredtext')
    pub.reader.doc_format = doc_format
    pub.set_writer('null')
    pub.parser = pub.reader.parser
    pub.process_programmatic_settings(None, None, None)
    pub.set_source(source, None)
    pub.set_destination(None, None)
    output = pub.publish(enable_exit_status=False)
    return pub.document


class DocstringFormat:
    name = ''
    sections = None  # type: List[str]

    def __init__(self, line, logger=None):
        """
        Parameters
        ----------
        line : int
        logger 
        """
        self.logger = logger or _logger
        self.line = line

    def warning(self, message, line):
        """
        Parameters
        ----------
        message : str
        line : int
        """
        extra = {
            'line': line + self.line,
            'column': 0
        }
        self.logger.warning(message, extra=extra)

    def error(self, message, line):
        """
        Parameters
        ----------
        message : str
        line : int
        """
        extra = {
            'line': line + self.line,
            'column': 0
        }
        self.logger.error(message, extra=extra)

    @classmethod
    def matches(cls, docstring):
        """
        Parameters
        ----------
        docstring : str

        Returns
        -------
        bool
        """
        return any(s.search(docstring) for s in cls.sections)

    def parse(self, docstring):
        """
        Parameters
        ----------
        docstring : str

        Returns
        -------
        Tuple[Dict[str, Arg], Optional[Arg]]
        """
        raise NotImplementedError


class RestBaseFormat(DocstringFormat):
    """
    Base class for all types that convert to restructuredText as a common parsing format
    """
    config = Config(napoleon_use_param=True, napoleon_use_rtype=True)

    def to_rest(self, docstring):
        """
        Convert a docstring from the native format to rest

        Parameters
        ----------
        docstring : str

        Returns
        -------
        str
        """
        raise NotImplementedError

    def parse(self, docstring):
        """
        Parameters
        ----------
        docstring : str

        Returns
        -------
        Tuple[Dict[str, Arg], Optional[Arg]]
        """
        docstring = self.to_rest(docstring)
        params = OrderedDict()
        result = None  # type: Arg

        try:
            document = publish_doctree(docstring, self)
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
                    self.warning(NAMED_ITEMS_ERROR, field.line)
            elif len(parts) == 1 or (len(parts) == 2 and parts[0] == 'type'):
                paragraph = field.traverse(condition=docutils.nodes.paragraph)[0]
                arg = Arg(_clean_type(paragraph.astext()), paragraph.line)
                if len(parts) == 2:
                    # e.g. :type foo: xxxx
                    kind, name = parts
                    params[name] = arg
                elif len(parts) == 1 and parts[0] == 'rtype':
                    # e.g. :rtype: xxxx
                    result = arg
                elif len(parts) == 1 and parts[0] == 'Yields':
                    # e.g. converted from numpy or google format
                    self.warning(YIELDS_ERROR, paragraph.line)

        return params, result


class RestFormat(RestBaseFormat):
    name = 'rest'
    sections = compile(
        r'(\n|^):param ',
        r'(\n|^):rtype:',
        r'(\n|^):Yields:'
    )

    def to_rest(self, docstring):
        return _cleandoc(docstring)


class NumpyFormat(RestBaseFormat):
    name = 'numpy'
    sections = compile(
        r'(\n|^)Parameters\n----------\n',
        r'(\n|^)Returns\n-------\n',
        r'(\n|^)Yields\n------\n'
    )

    def to_rest(self, docstring):
        return str(NumpyDocstring(_cleandoc(docstring), self.config))


class GoogleFormat(RestBaseFormat):
    name = 'google'
    sections = compile(
        r'(\n|^)Args:\n',
        r'(\n|^)Returns:\n',
        r'(\n|^)Yields:\n'
    )

    def to_rest(self, docstring):
        return str(GoogleDocstring(_cleandoc(docstring), self.config))


default_format = RestFormat
formats = [NumpyFormat, GoogleFormat, default_format]  # type: List[DocstringFormat]
format_map = {f.name: f for f in formats}  # type: Dict[str, DocstringFormat]


def guess_format(docstring):
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


def parse_docstring(docstring, line=0, logger=None, default_format='auto'):
    """
    Parameters
    ----------
    docstring : str
    line : int

    Returns
    -------
    Tuple[Dict[str, Arg], Optional[Arg]]
    """
    if default_format == 'auto':
        format = guess_format(docstring)
    else:
        format = format_map[default_format]
    return format(line, logger).parse(docstring)
