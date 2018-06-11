from __future__ import absolute_import, print_function
import re
import inspect
import logging
from collections import OrderedDict

from typing import List, Tuple, Dict, Optional, TYPE_CHECKING, Type as Class

from doc484.parsers import Arg
from doc484.parsers.other import GoogleDocstring, NumpyDocstring
from doc484.parsers.rest import RestDocstring

YIELDS_ERROR = "'Yields' is not supported. Use 'Returns' with Iterator[]"
NAMED_ITEMS_ERROR = 'Named results are not supported. Use Tuple[] or NamedTuple'
NAMED_RESULTS_REG = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*\s+\(([^)]+)\)')

logging.basicConfig()

_logger = logging.getLogger(__name__)


def _setup_logger(log):
    log.propagate = False
    hdlr = logging.StreamHandler()
    fmt = logging.Formatter('%(file)s: line %(line)s: %(message)s')
    hdlr.setFormatter(fmt)
    log.addHandler(hdlr)


def _cleandoc(docstring):
    return inspect.cleandoc(docstring).replace('`', '')


def compile(*regexs):
    # type: (str) -> List[re.Pattern]
    return [re.compile(s) for s in regexs]


class DocstringFormat(object):
    name = ''
    sections = None  # type: List[str]

    def __init__(self, line, filename='<string>', logger=None, options=None):
        """
        Parameters
        ----------
        line : int
            start line of the docstring
        logger : Optional[logging.Logger]
        """
        self.logger = logger or _logger
        self.line = line
        self.filename = filename
        self.options = options or {}

    def warning(self, message, line):
        """
        Parameters
        ----------
        message : str
        line : int
        """
        extra = {
            'file': self.filename,
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
            'file': self.filename,
            'line': line + self.line,
            'column': 0
        }
        self.logger.error(message, extra=extra)

    @classmethod
    def matches(cls, docstring):
        """
        Return whether `docstring` is compatible with this format.

        Parameters
        ----------
        docstring : str

        Returns
        -------
        bool
        """
        return any(s.search(docstring) for s in cls.sections)

    def _cast_pararms(self, params):
        if params is not None:
            return OrderedDict(params)
        else:
            return OrderedDict()

    def _cast_returns(self, _returns):
        if not _returns:
            return None
        elif len(_returns) == 1:
            return _returns[0]
        else:
            if self.options.get('allow_named_results', True):
                return Arg('Tuple[%s]' % ', '.join([x.type for x in _returns]),
                           _returns[0].line)
            else:
                self.warning(NAMED_ITEMS_ERROR, _returns[0].line)

    def get_parser(self, docstring):
        raise NotImplementedError

    def parse(self, docstring):
        """
        Parameters
        ----------
        docstring : str

        Returns
        -------
        Tuple[OrderedDict[str, Arg], Optional[Arg]]
        """
        p = self.get_parser(_cleandoc(docstring))
        params, _returns, _yields = p.parse()
        if _yields:
            self.warning(YIELDS_ERROR, _yields[0].line)
        return self._cast_pararms(params), self._cast_returns(_returns)


class RestFormat(DocstringFormat):

    name = 'rest'
    sections = compile(
        r'(\n|^):param ',
        r'(\n|^):rtype:',
        r'(\n|^):Yields:'
    )

    parser = RestDocstring

    def get_parser(self, docstring):
        return self.parser(docstring, self)


class NumpyFormat(DocstringFormat):
    name = 'numpy'
    sections = compile(
        r'(\n|^)Parameters\n----------\n',
        r'(\n|^)Returns\n-------\n',
        r'(\n|^)Yields\n------\n'
    )
    parser = NumpyDocstring

    def get_parser(self, docstring):
        return self.parser(docstring)


class GoogleFormat(DocstringFormat):
    name = 'google'
    sections = compile(
        r'(\n|^)Args:\n',
        r'(\n|^)Returns:\n',
        r'(\n|^)Yields:\n'
    )
    parser = GoogleDocstring

    def get_parser(self, docstring):
        return self.parser(docstring)


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


def parse_docstring(docstring, line=0, filename='<string>', logger=None,
                    default_format='auto', options=None):
    """
    Parameters
    ----------
    docstring : str
    line : int

    Returns
    -------
    Tuple[OrderedDict[str, Arg], Optional[Arg]]
    """
    if default_format == 'auto':
        format_cls = guess_format(docstring)
    else:
        format_cls = format_map[default_format]
    format = format_cls(line, filename=filename, logger=logger,
                        options=options)
    return format.parse(docstring)


_setup_logger(_logger)
