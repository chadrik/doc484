from __future__ import absolute_import, print_function
import re
import inspect
import logging
from collections import OrderedDict

from doc484.parsers import Arg
from doc484.parsers.other import GoogleDocstring, NumpyDocstring
from doc484.parsers.rest import RestDocstring

if False:
    from typing import *

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
    # type: (str) -> str
    return inspect.cleandoc(docstring).replace('`', '')


def compile(*regexs):
    # type: (str) -> List[re.Pattern]
    return [re.compile(s) for s in regexs]


class DocstringFormat(object):
    name = None  # type: str
    sections = None  # type: List[str]

    def __init__(self, line, filename='<string>', logger=None, options=None):
        # type: (int, Any, Optional[logging.Logger], Any) -> None
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
        # type: (str, int) -> None
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
        # type: (str, int) -> None
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
        # type: (str) -> bool
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
        # type: (Optional[Iterable[Tuple[str, Arg]]]) -> OrderedDict[str, Arg]
        """
        Parameters
        ----------
        params : Optional[Iterable[Tuple[str, Arg]]]

        Returns
        -------
        OrderedDict[str, Arg]
        """
        if params is not None:
            return OrderedDict(params)
        else:
            return OrderedDict()

    def _cast_returns(self, returns):
        # type: (Optional[List[Arg]]) -> Arg
        """
        Parameters
        ----------
        returns : Optional[List[Arg]]

        Returns
        -------
        Arg
        """
        if not returns:
            return None
        elif len(returns) == 1:
            return returns[0]
        else:
            if self.options.get('allow_named_results', True):
                return Arg('Tuple[%s]' % ', '.join([x.type for x in returns]),
                           returns[0].line)
            else:
                self.warning(NAMED_ITEMS_ERROR, returns[0].line)

    def get_parser(self, docstring):
        raise NotImplementedError

    def parse(self, docstring):
        # type: (str) -> Tuple[OrderedDict[str, Arg], Optional[Arg]]
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


_default_format = None  # type: Optional[Type[DocstringFormat]]
formats = [NumpyFormat, GoogleFormat, RestFormat]  # type: List[Type[DocstringFormat]]
format_map = {f.name: f for f in formats}  # type: Dict[str, Type[DocstringFormat]]


def set_default_format(format_name):
    # type: (Optional[str]) -> Optional[Type[DocstringFormat]]
    """
    Parameters
    ----------
    format_name : Optional[str]

    Returns
    -------
    Optional[Type[DocstringFormat]]
    """
    global _default_format
    if format_name is None:
        _default_format = None
    _default_format = format_map[format_name]
    return _default_format


def get_default_format():
    # type: () -> Optional[Type[DocstringFormat]]
    """
    Returns
    -------
    Optional[Type[DocstringFormat]]
    """
    return _default_format


def guess_format(docstring):
    # type: (str) -> Type[DocstringFormat]
    """
    Convert the passed docstring to reStructuredText format.

    Parameters
    ----------
    docstring : str
        the docstring to convert

    Returns
    -------
    Type[DocstringFormat]
    """
    docstring = inspect.cleandoc(docstring)
    for format in formats:
        if format.matches(docstring):
            return format
    return default_format


def parse_docstring(docstring, line=0, filename='<string>', logger=None,
                    default_format=None, options=None):
    # type: (str, int, Any, Optional[logging.Logger], Optional[str], Any) -> Tuple[OrderedDict[str, Arg], Optional[Arg]]
    """
    Parameters
    ----------
    docstring : str
    line : int
        start line of the docstring
    logger : Optional[logging.Logger]
    default_format : Optional[str]

    Returns
    -------
    Tuple[OrderedDict[str, Arg], Optional[Arg]]
    """
    if default_format is None:
        # fall back to the global default (as set by set_default_format)
        fmt = get_default_format()
        if fmt is None:
            format_cls = guess_format(docstring)
        else:
            format_cls = fmt
    else:
        format_cls = format_map[default_format]
    format = format_cls(line, filename=filename, logger=logger,
                        options=options)
    return format.parse(docstring)


_setup_logger(_logger)
