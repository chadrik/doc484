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

YIELDS_ERROR = "'Yields' is not allowed. Use 'Returns' with Iterator[], " \
               "or enable allow_yields"
NAMED_ITEMS_ERROR = 'Named results are not allowed. Use Tuple[] or ' \
                    'NamedTuple, or enable allow_named_results'
NAMED_RESULTS_REG = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*\s+\(([^)]+)\)')

# logging.basicConfig()

_logger = None

# mapping of arg -> type annotation
default_arg_types = {}  # type: Dict[str, str]
default_return_type = 'Any'


class FormatLoggingAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        line = self.extra['line'] + kwargs['extra']['line']
        return u'%s: line %s: %s' % (self.extra['file'], line, msg), kwargs


def get_deafult_logger():
    # let's us defer creation of the logger until basicConfig is called by
    # main()
    global _logger
    # FIXME: conditionally run basicConfig?
    if _logger is None:
        _logger = logging.getLogger(__name__)
    return _logger


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
        assert logger is None
        self.logger = FormatLoggingAdapter(
            logger or get_deafult_logger(),
            extra={
                'file': filename,
                'line': line,
                'column': 0
            }
        )
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
            'line': line,
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
            'line': line,
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
        # type: (Optional[List[Arg]]) -> Optional[Arg]
        """
        Parameters
        ----------
        returns : Optional[List[Arg]]

        Returns
        -------
        Optional[Arg]
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

    def _cast_yields(self, yields):
        # type: (Optional[List[Arg]]) -> Optional[Arg]
        """
        Parameters
        ----------
        yields : Optional[List[Arg]]

        Returns
        -------
        Optional[Arg]
        """
        if not yields:
            return None

        if self.options.get('allow_yields', True):
            result = self._cast_returns(yields)
            if result:
                return Arg('Iterator[%s]' % result.type, result.line)
        else:
            self.warning(YIELDS_ERROR, yields[0].line)

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
        params, returns, yields = p.parse()
        if returns and yields:
            self.warning("types found for both return and yield",
                         returns[0].line)
        if yields:
            result = self._cast_yields(yields)
        elif returns:
            result = self._cast_returns(returns)
        else:
            result = None
        return self._cast_pararms(params), result


class RestFormat(DocstringFormat):

    name = 'rest'
    sections = compile(
        r'(\n|^):param ',
        r'(\n|^):rtype:',
        r'(\n|^):Yields:'
    )

    parser_class = RestDocstring

    def get_parser(self, docstring):
        return self.parser_class(docstring, self)


class NumpyFormat(DocstringFormat):
    name = 'numpy'
    sections = compile(
        r'(\n|^)Parameters\n----------\n',
        r'(\n|^)Returns\n-------\n',
        r'(\n|^)Yields\n------\n'
    )
    parser_class = NumpyDocstring

    def get_parser(self, docstring):
        return self.parser_class(docstring)


class GoogleFormat(DocstringFormat):
    name = 'google'
    sections = compile(
        r'(\n|^)Args:\n',
        r'(\n|^)Returns:\n',
        r'(\n|^)Yields:\n'
    )
    parser_class = GoogleDocstring

    def get_parser(self, docstring):
        return self.parser_class(docstring)


default_format = None  # type: Optional[Type[DocstringFormat]]
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
    global default_format
    if format_name is None:
        default_format = None
    default_format = format_map[format_name]
    return default_format


def get_default_format():
    # type: () -> Optional[Type[DocstringFormat]]
    """
    Returns
    -------
    Optional[Type[DocstringFormat]]
    """
    return default_format


def guess_format(docstring):
    # type: (str) -> Optional[Type[DocstringFormat]]
    """
    Convert the passed docstring to reStructuredText format.

    Parameters
    ----------
    docstring : str
        the docstring to convert

    Returns
    -------
    Optional[Type[DocstringFormat]]
    """
    docstring = inspect.cleandoc(docstring)
    for format in formats:
        if format.matches(docstring):
            return format


def parse_docstring(docstring, line=0, filename='<string>', logger=None,
                    format_name=None, options=None):
    # type: (str, int, Any, Optional[logging.Logger], Optional[str], Any) -> Tuple[OrderedDict[str, Arg], Optional[Arg]]
    """
    Parse the passed docstring.

    The OrderedDict holding parsed parameters may be sparse.

    Parameters
    ----------
    docstring : str
    line : int
        start line of the docstring
    logger : Optional[logging.Logger]
    format_name : Optional[str]

    Returns
    -------
    Tuple[OrderedDict[str, Arg], Optional[Arg]]
    """
    if format_name is None:
        # fall back to the global default (as set by set_default_format)
        format_cls = get_default_format()
        if format_cls is None:
            format_cls = guess_format(docstring)
            if format_cls is None:
                format_cls = RestFormat
    else:
        format_cls = format_map[format_name]
    format = format_cls(line, filename=filename, logger=logger,
                        options=options)
    return format.parse(docstring)
