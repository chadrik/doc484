# License for Sphinx
# ==================
#
# Copyright (c) 2007-2017 by the Sphinx team (see AUTHORS file).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, print_function


import collections
import re

from six import string_types, u
from six.moves import range
from six import PY3


if PY3:
    class UnicodeMixin:
        """Mixin class to handle defining the proper __str__/__unicode__
        methods in Python 2 or 3."""

        def __str__(self):
            return self.__unicode__()


else:

    class UnicodeMixin(object):
        """Mixin class to handle defining the proper __str__/__unicode__
        methods in Python 2 or 3."""

        def __str__(self):
            return self.__unicode__().encode('utf8')


_directive_regex = re.compile(r'\.\. \S+::')
_google_section_regex = re.compile(r'^(\s|\w)+:\s*$')
_google_typed_arg_regex = re.compile(r'\s*(.+?)\s*\(\s*(.+?)\s*\)')
_numpy_section_regex = re.compile(r'^[=\-`:\'"~^_*+#<>]{2,}\s*$')
_xref_regex = re.compile(r'(:\w+:\S+:`.+?`|:\S+:`.+?`|`.+?`)')
_bullet_list_regex = re.compile(r'^(\*|\+|\-)(\s+\S|\s*$)')
_enumerated_list_regex = re.compile(
    r'^(?P<paren>\()?'
    r'(\d+|#|[ivxlcdm]+|[IVXLCDM]+|[a-zA-Z])'
    r'(?(paren)\)|\.)(\s+\S|\s*$)')


class Config(object):
    """Sphinx napoleon extension settings in `conf.py`.

    Listed below are all the settings used by napoleon and their default
    values. These settings can be changed in the Sphinx `conf.py` file. Make
    sure that both "sphinx.ext.autodoc" and "sphinx.ext.napoleon" are
    enabled in `conf.py`::

        # conf.py

        # Add any Sphinx extension module names here, as strings
        extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

        # Napoleon settings
        napoleon_google_docstring = True
        napoleon_numpy_docstring = True
        napoleon_include_private_with_doc = False
        napoleon_include_special_with_doc = False
        napoleon_use_admonition_for_examples = False
        napoleon_use_admonition_for_notes = False
        napoleon_use_admonition_for_references = False
        napoleon_use_ivar = False
        napoleon_use_param = True
        napoleon_use_rtype = True

    .. _Google style:
       http://google.github.io/styleguide/pyguide.html
    .. _NumPy style:
       https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

    Attributes
    ----------
    napoleon_google_docstring : bool, defaults to True
        True to parse `Google style`_ docstrings. False to disable support
        for Google style docstrings.
    napoleon_numpy_docstring : bool, defaults to True
        True to parse `NumPy style`_ docstrings. False to disable support
        for NumPy style docstrings.
    napoleon_include_private_with_doc : bool, defaults to False
        True to include private members (like ``_membername``) with docstrings
        in the documentation. False to fall back to Sphinx's default behavior.

        **If True**::

            def _included(self):
                \"\"\"
                This will be included in the docs because it has a docstring
                \"\"\"
                pass

            def _skipped(self):
                # This will NOT be included in the docs
                pass

    napoleon_include_special_with_doc : bool, defaults to False
        True to include special members (like ``__membername__``) with
        docstrings in the documentation. False to fall back to Sphinx's
        default behavior.

        **If True**::

            def __str__(self):
                \"\"\"
                This will be included in the docs because it has a docstring
                \"\"\"
                return unicode(self).encode('utf-8')

            def __unicode__(self):
                # This will NOT be included in the docs
                return unicode(self.__class__.__name__)

    napoleon_use_admonition_for_examples : bool, defaults to False
        True to use the ``.. admonition::`` directive for the **Example** and
        **Examples** sections. False to use the ``.. rubric::`` directive
        instead. One may look better than the other depending on what HTML
        theme is used.

        This `NumPy style`_ snippet will be converted as follows::

            Example
            -------
            This is just a quick example

        **If True**::

            .. admonition:: Example

               This is just a quick example

        **If False**::

            .. rubric:: Example

            This is just a quick example

    napoleon_use_admonition_for_notes : bool, defaults to False
        True to use the ``.. admonition::`` directive for **Notes** sections.
        False to use the ``.. rubric::`` directive instead.

        Note
        ----
        The singular **Note** section will always be converted to a
        ``.. note::`` directive.

        See Also
        --------
        :attr:`napoleon_use_admonition_for_examples`

    napoleon_use_admonition_for_references : bool, defaults to False
        True to use the ``.. admonition::`` directive for **References**
        sections. False to use the ``.. rubric::`` directive instead.

        See Also
        --------
        :attr:`napoleon_use_admonition_for_examples`

    napoleon_use_ivar : bool, defaults to False
        True to use the ``:ivar:`` role for instance variables. False to use
        the ``.. attribute::`` directive instead.

        This `NumPy style`_ snippet will be converted as follows::

            Attributes
            ----------
            attr1 : int
                Description of `attr1`

        **If True**::

            :ivar attr1: Description of `attr1`
            :vartype attr1: int

        **If False**::

            .. attribute:: attr1

               *int*

               Description of `attr1`

    napoleon_use_param : bool, defaults to True
        True to use a ``:param:`` role for each function parameter. False to
        use a single ``:parameters:`` role for all the parameters.

        This `NumPy style`_ snippet will be converted as follows::

            Parameters
            ----------
            arg1 : str
                Description of `arg1`
            arg2 : int, optional
                Description of `arg2`, defaults to 0

        **If True**::

            :param arg1: Description of `arg1`
            :type arg1: str
            :param arg2: Description of `arg2`, defaults to 0
            :type arg2: int, optional

        **If False**::

            :parameters: * **arg1** (*str*) --
                           Description of `arg1`
                         * **arg2** (*int, optional*) --
                           Description of `arg2`, defaults to 0

    napoleon_use_rtype : bool, defaults to True
        True to use the ``:rtype:`` role for the return type. False to output
        the return type inline with the description.

        This `NumPy style`_ snippet will be converted as follows::

            Returns
            -------
            bool
                True if successful, False otherwise

        **If True**::

            :returns: True if successful, False otherwise
            :rtype: bool

        **If False**::

            :returns: *bool* -- True if successful, False otherwise

    """
    _config_values = {
        'napoleon_google_docstring': (True, 'env'),
        'napoleon_numpy_docstring': (True, 'env'),
        'napoleon_include_private_with_doc': (False, 'env'),
        'napoleon_include_special_with_doc': (False, 'env'),
        'napoleon_use_admonition_for_examples': (False, 'env'),
        'napoleon_use_admonition_for_notes': (False, 'env'),
        'napoleon_use_admonition_for_references': (False, 'env'),
        'napoleon_use_ivar': (False, 'env'),
        'napoleon_use_param': (True, 'env'),
        'napoleon_use_rtype': (True, 'env'),
    }

    def __init__(self, **settings):
        for name, (default, rebuild) in self._config_values.items():
            setattr(self, name, default)
        for name, value in settings.items():
            setattr(self, name, value)


class peek_iter(object):
    """An iterator object that supports peeking ahead.

    Parameters
    ----------
    o : iterable or callable
        `o` is interpreted very differently depending on the presence of
        `sentinel`.

        If `sentinel` is not given, then `o` must be a collection object
        which supports either the iteration protocol or the sequence protocol.

        If `sentinel` is given, then `o` must be a callable object.

    sentinel : any value, optional
        If given, the iterator will call `o` with no arguments for each
        call to its `next` method; if the value returned is equal to
        `sentinel`, :exc:`StopIteration` will be raised, otherwise the
        value will be returned.

    See Also
    --------
    `peek_iter` can operate as a drop in replacement for the built-in
    `iter <https://docs.python.org/2/library/functions.html#iter>`_ function.

    Attributes
    ----------
    sentinel
        The value used to indicate the iterator is exhausted. If `sentinel`
        was not given when the `peek_iter` was instantiated, then it will
        be set to a new object instance: ``object()``.

    """
    def __init__(self, *args):
        """__init__(o, sentinel=None)"""
        self._iterable = iter(*args)
        self._cache = collections.deque()
        if len(args) == 2:
            self.sentinel = args[1]
        else:
            self.sentinel = object()

    def __iter__(self):
        return self

    def __next__(self, n=None):
        # note: prevent 2to3 to transform self.next() in next(self) which
        # causes an infinite loop !
        return getattr(self, 'next')(n)

    def _fillcache(self, n):
        """Cache `n` items. If `n` is 0 or None, then 1 item is cached."""
        if not n:
            n = 1
        try:
            while len(self._cache) < n:
                self._cache.append(next(self._iterable))
        except StopIteration:
            while len(self._cache) < n:
                self._cache.append(self.sentinel)

    def has_next(self):
        """Determine if iterator is exhausted.

        Returns
        -------
        bool
            True if iterator has more items, False otherwise.

        Note
        ----
        Will never raise :exc:`StopIteration`.

        """
        return self.peek() != self.sentinel

    def next(self, n=None):
        """Get the next item or `n` items of the iterator.

        Parameters
        ----------
        n : int or None
            The number of items to retrieve. Defaults to None.

        Returns
        -------
        item or list of items
            The next item or `n` items of the iterator. If `n` is None, the
            item itself is returned. If `n` is an int, the items will be
            returned in a list. If `n` is 0, an empty list is returned.

        Raises
        ------
        StopIteration
            Raised if the iterator is exhausted, even if `n` is 0.

        """
        self._fillcache(n)
        if not n:
            if self._cache[0] == self.sentinel:
                raise StopIteration
            if n is None:
                result = self._cache.popleft()
            else:
                result = []
        else:
            if self._cache[n - 1] == self.sentinel:
                raise StopIteration
            result = [self._cache.popleft() for i in range(n)]
        return result

    def peek(self, n=None):
        """Preview the next item or `n` items of the iterator.

        The iterator is not advanced when peek is called.

        Returns
        -------
        item or list of items
            The next item or `n` items of the iterator. If `n` is None, the
            item itself is returned. If `n` is an int, the items will be
            returned in a list. If `n` is 0, an empty list is returned.

            If the iterator is exhausted, `peek_iter.sentinel` is returned,
            or placed as the last item in the returned list.

        Note
        ----
        Will never raise :exc:`StopIteration`.

        """
        self._fillcache(n)
        if n is None:
            result = self._cache[0]
        else:
            result = [self._cache[i] for i in range(n)]
        return result


class modify_iter(peek_iter):
    """An iterator object that supports modifying items as they are returned.

    Parameters
    ----------
    o : iterable or callable
        `o` is interpreted very differently depending on the presence of
        `sentinel`.

        If `sentinel` is not given, then `o` must be a collection object
        which supports either the iteration protocol or the sequence protocol.

        If `sentinel` is given, then `o` must be a callable object.

    sentinel : any value, optional
        If given, the iterator will call `o` with no arguments for each
        call to its `next` method; if the value returned is equal to
        `sentinel`, :exc:`StopIteration` will be raised, otherwise the
        value will be returned.

    modifier : callable, optional
        The function that will be used to modify each item returned by the
        iterator. `modifier` should take a single argument and return a
        single value. Defaults to ``lambda x: x``.

        If `sentinel` is not given, `modifier` must be passed as a keyword
        argument.

    Attributes
    ----------
    modifier : callable
        `modifier` is called with each item in `o` as it is iterated. The
        return value of `modifier` is returned in lieu of the item.

        Values returned by `peek` as well as `next` are affected by
        `modifier`. However, `modify_iter.sentinel` is never passed through
        `modifier`; it will always be returned from `peek` unmodified.

    Example
    -------
    >>> a = ["     A list    ",
    ...      "   of strings  ",
    ...      "      with     ",
    ...      "      extra    ",
    ...      "   whitespace. "]
    >>> modifier = lambda s: s.strip().replace('with', 'without')
    >>> for s in modify_iter(a, modifier=modifier):
    ...   print('"%s"' % s)
    "A list"
    "of strings"
    "without"
    "extra"
    "whitespace."

    """
    def __init__(self, *args, **kwargs):
        """__init__(o, sentinel=None, modifier=lambda x: x)"""
        if 'modifier' in kwargs:
            self.modifier = kwargs['modifier']
        elif len(args) > 2:
            self.modifier = args[2]
            args = args[:2]
        else:
            self.modifier = lambda x: x
        if not callable(self.modifier):
            raise TypeError('modify_iter(o, modifier): '
                            'modifier must be callable')
        super(modify_iter, self).__init__(*args)

    def _fillcache(self, n):
        """Cache `n` modified items. If `n` is 0 or None, 1 item is cached.

        Each item returned by the iterator is passed through the
        `modify_iter.modified` function before being cached.

        """
        if not n:
            n = 1
        try:
            while len(self._cache) < n:
                self._cache.append(self.modifier(next(self._iterable)))
        except StopIteration:
            while len(self._cache) < n:
                self._cache.append(self.sentinel)


class GoogleDocstring(UnicodeMixin):
    """Convert Google style docstrings to reStructuredText.

    Parameters
    ----------
    docstring : str or List[str]
        The docstring to parse, given either as a string or split into
        individual lines.
    config : Optional[sphinx.ext.napoleon.Config or sphinx.config.Config]
        The configuration settings to use. If not given, defaults to the
        config object on `app`; or if `app` is not given defaults to the
        a new `sphinx.ext.napoleon.Config` object.

        See Also
        --------
        :class:`sphinx.ext.napoleon.Config`

    Other Parameters
    ----------------
    app : Optional[sphinx.application.Sphinx]
        Application object representing the Sphinx process.
    what : Optional[str]
        A string specifying the type of the object to which the docstring
        belongs. Valid values: "module", "class", "exception", "function",
        "method", "attribute".
    name : Optional[str]
        The fully qualified name of the object.
    obj : module, class, exception, function, method, or attribute
        The object to which the docstring belongs.
    options : Optional[sphinx.ext.autodoc.Options]
        The options given to the directive: an object with attributes
        inherited_members, undoc_members, show_inheritance and noindex that
        are True if the flag option of same name was given to the auto
        directive.

    Example
    -------
    >>> from sphinx.ext.napoleon import Config
    >>> config = Config(napoleon_use_param=True, napoleon_use_rtype=True)
    >>> docstring = '''One line summary.
    ...
    ... Extended description.
    ...
    ... Args:
    ...   arg1(int): Description of `arg1`
    ...   arg2(str): Description of `arg2`
    ... Returns:
    ...   str: Description of return value.
    ... '''
    >>> print(GoogleDocstring(docstring, config))
    One line summary.
    <BLANKLINE>
    Extended description.
    <BLANKLINE>
    :param arg1: Description of `arg1`
    :type arg1: int
    :param arg2: Description of `arg2`
    :type arg2: str
    <BLANKLINE>
    :returns: Description of return value.
    :rtype: str
    <BLANKLINE>

    """
    _directive_sections = []

    def __init__(self, docstring, config=None):
        self._config = config

        if not self._config:
            self._config = Config()

        if isinstance(docstring, string_types):
            docstring = docstring.splitlines()
        self._lines = docstring
        self._line_iter = modify_iter(docstring, modifier=lambda s: s.rstrip())
        self._parsed_lines = []
        self._is_in_section = False
        self._section_indent = 0

        self._sections = {
            'args': self._parse_parameters_section,
            'arguments': self._parse_parameters_section,
            'attributes': self._skip_section,
            'example': self._skip_section,
            'examples': self._skip_section,
            'keyword args': self._skip_section,
            'keyword arguments': self._skip_section,
            'methods': self._skip_section,
            'note': self._skip_section,
            'notes': self._skip_section,
            'other parameters': self._skip_section,
            'parameters': self._parse_parameters_section,
            'return': self._parse_returns_section,
            'returns': self._parse_returns_section,
            'raises': self._skip_section,
            'references': self._skip_section,
            'see also': self._skip_section,
            'todo': self._skip_section,
            'warning': self._skip_section,
            'warnings': self._skip_section,
            'warns': self._skip_section,
            'yield': self._parse_yields_section,
            'yields': self._parse_yields_section,
        }

    def __unicode__(self):
        """Return the parsed docstring in reStructuredText format.

        Returns
        -------
        unicode
            Unicode version of the docstring.

        """
        return u('\n').join(self.lines())

    def lines(self):
        """Return the parsed lines of the docstring in reStructuredText format.

        Returns
        -------
        List[str]
            The lines of the docstring in a list.

        """
        return self._parsed_lines

    def _consume_indented_block(self, indent=1):
        lines = []
        line = self._line_iter.peek()
        while(not self._is_section_break() and
              (not line or self._is_indented(line, indent))):
            lines.append(next(self._line_iter))
            line = self._line_iter.peek()
        return lines

    def _consume_contiguous(self):
        lines = []
        while (self._line_iter.has_next() and
               self._line_iter.peek() and
               not self._is_section_header()):
            lines.append(next(self._line_iter))
        return lines

    def _consume_empty(self):
        lines = []
        line = self._line_iter.peek()
        while self._line_iter.has_next() and not line:
            lines.append(next(self._line_iter))
            line = self._line_iter.peek()
        return lines

    def _consume_field(self, parse_type=True, prefer_type=False):
        line = next(self._line_iter)

        before, colon, after = self._partition_field_on_colon(line)
        _name, _type, _desc = before, '', after

        if parse_type:
            match = _google_typed_arg_regex.match(before)
            if match:
                _name = match.group(1)
                _type = match.group(2)

        _name = self._escape_args_and_kwargs(_name)

        if prefer_type and not _type:
            _type, _name = _name, _type
        indent = self._get_indent(line) + 1
        self._consume_indented_block(indent)
        return _name, _type

    def _consume_fields(self, parse_type=True, prefer_type=False):
        self._consume_empty()
        fields = []
        while not self._is_section_break():
            _name, _type = self._consume_field(parse_type, prefer_type)
            if _name or _type:
                fields.append((_name, _type,))
        return fields

    def _consume_returns_section(self):
        lines = self._dedent(self._consume_to_next_section())
        if lines:
            before, colon, after = self._partition_field_on_colon(lines[0])
            _name, _type, _desc = '', '', lines

            if colon:
                match = _google_typed_arg_regex.match(before)
                if match:
                    _name = match.group(1)
                    _type = match.group(2)
                else:
                    _type = before

            return [(_name, _type,)]
        else:
            return []

    def _consume_section_header(self):
        section = next(self._line_iter)
        stripped_section = section.strip(':')
        if stripped_section.lower() in self._sections:
            section = stripped_section
        return section

    def _consume_to_end(self):
        lines = []
        while self._line_iter.has_next():
            lines.append(next(self._line_iter))
        return lines

    def _consume_to_next_section(self):
        self._consume_empty()
        lines = []
        while not self._is_section_break():
            lines.append(next(self._line_iter))
        return lines + self._consume_empty()

    def _dedent(self, lines, full=False):
        if full:
            return [line.lstrip() for line in lines]
        else:
            min_indent = self._get_min_indent(lines)
            return [line[min_indent:] for line in lines]

    def _escape_args_and_kwargs(self, name):
        if name[:2] == '**':
            return r'\*\*' + name[2:]
        elif name[:1] == '*':
            return r'\*' + name[1:]
        else:
            return name

    def _format_admonition(self, admonition, lines):
        lines = self._strip_empty(lines)
        if len(lines) == 1:
            return ['.. %s:: %s' % (admonition, lines[0].strip()), '']
        elif lines:
            lines = self._indent(self._dedent(lines), 3)
            return ['.. %s::' % admonition, ''] + lines + ['']
        else:
            return ['.. %s::' % admonition, '']

    def _format_block(self, prefix, lines, padding=None):
        if lines:
            if padding is None:
                padding = ' ' * len(prefix)
            result_lines = []
            for i, line in enumerate(lines):
                if i == 0:
                    result_lines.append((prefix + line).rstrip())
                elif line:
                    result_lines.append(padding + line)
                else:
                    result_lines.append('')
            return result_lines
        else:
            return [prefix]

    def _format_field(self, _name, _type):
        separator = ''
        if _name:
            if _type:
                if '`' in _type:
                    field = '**%s** (%s)%s' % (_name, _type, separator)
                else:
                    field = '**%s** (*%s*)%s' % (_name, _type, separator)
            else:
                field = '**%s**%s' % (_name, separator)
        elif _type:
            if '`' in _type:
                field = '%s%s' % (_type, separator)
            else:
                field = '*%s*%s' % (_type, separator)
        else:
            field = ''

        return [field]

    def _format_fields(self, field_type, fields):
        field_type = ':%s:' % field_type.strip()
        padding = ' ' * len(field_type)
        multi = len(fields) > 1
        lines = []
        for _name, _type in fields:
            field = self._format_field(_name, _type)
            if multi:
                if lines:
                    lines.extend(self._format_block(padding + ' * ', field))
                else:
                    lines.extend(self._format_block(field_type + ' * ', field))
            else:
                lines.extend(self._format_block(field_type + ' ', field))
        if lines and lines[-1]:
            lines.append('')
        return lines

    def _get_current_indent(self, peek_ahead=0):
        line = self._line_iter.peek(peek_ahead + 1)[peek_ahead]
        while line != self._line_iter.sentinel:
            if line:
                return self._get_indent(line)
            peek_ahead += 1
            line = self._line_iter.peek(peek_ahead + 1)[peek_ahead]
        return 0

    def _get_indent(self, line):
        for i, s in enumerate(line):
            if not s.isspace():
                return i
        return len(line)

    def _get_min_indent(self, lines):
        min_indent = None
        for line in lines:
            if line:
                indent = self._get_indent(line)
                if min_indent is None:
                    min_indent = indent
                elif indent < min_indent:
                    min_indent = indent
        return min_indent or 0

    def _indent(self, lines, n=4):
        return [(' ' * n) + line for line in lines]

    def _is_indented(self, line, indent=1):
        for i, s in enumerate(line):
            if i >= indent:
                return True
            elif not s.isspace():
                return False
        return False

    def _is_list(self, lines):
        if not lines:
            return False
        if _bullet_list_regex.match(lines[0]):
            return True
        if _enumerated_list_regex.match(lines[0]):
            return True
        if len(lines) < 2 or lines[0].endswith('::'):
            return False
        indent = self._get_indent(lines[0])
        next_indent = indent
        for line in lines[1:]:
            if line:
                next_indent = self._get_indent(line)
                break
        return next_indent > indent

    def _is_section_header(self):
        section = self._line_iter.peek().lower()
        match = _google_section_regex.match(section)
        if match and section.strip(':') in self._sections:
            header_indent = self._get_indent(section)
            section_indent = self._get_current_indent(peek_ahead=1)
            return section_indent > header_indent
        elif self._directive_sections:
            if _directive_regex.match(section):
                for directive_section in self._directive_sections:
                    if section.startswith(directive_section):
                        return True
        return False

    def _is_section_break(self):
        line = self._line_iter.peek()
        return (not self._line_iter.has_next() or
                self._is_section_header() or
                (self._is_in_section and
                    line and
                    not self._is_indented(line, self._section_indent)))

    def parse(self):
        self._parsed_lines = self._consume_empty()

        while self._line_iter.has_next():
            if self._is_section_header():
                try:
                    section = self._consume_section_header()
                    self._is_in_section = True
                    self._section_indent = self._get_current_indent()
                    if _directive_regex.match(section):
                        lines = [section] + self._consume_to_next_section()
                    else:
                        lines = self._sections[section.lower()](section)
                finally:
                    self._is_in_section = False
                    self._section_indent = 0
            else:
                if not self._parsed_lines:
                    lines = self._consume_contiguous() + self._consume_empty()
                else:
                    lines = self._consume_to_next_section()
            self._parsed_lines.extend(lines)

    def _skip_section(self, section):
        self._consume_to_next_section()
        return []

    def _parse_parameters_section(self, section):
        fields = self._consume_fields()
        if self._config.napoleon_use_param:
            lines = []
            for _name, _type in fields:
                lines.append(':param %s:' % _name)

                if _type:
                    lines.append(':type %s: %s' % (_name, _type))

            return lines + ['']
        else:
            return self._format_fields('Parameters', fields)

    def _parse_returns_section(self, section):
        fields = self._consume_returns_section()
        multi = len(fields) > 1
        if multi:
            use_rtype = False
        else:
            use_rtype = self._config.napoleon_use_rtype

        lines = []
        for _name, _type in fields:
            if use_rtype:
                field = self._format_field(_name, '')
            else:
                field = self._format_field(_name, _type)

            if multi:
                if lines:
                    lines.extend(self._format_block('          * ', field))
                else:
                    lines.extend(self._format_block(':returns: * ', field))
            else:
                lines.extend(self._format_block(':returns: ', field))
                if _type and use_rtype:
                    lines.extend([':rtype: %s' % _type, ''])
        if lines and lines[-1]:
            lines.append('')
        return lines

    def _parse_yields_section(self, section):
        fields = self._consume_returns_section()
        return self._format_fields('Yields', fields)

    def _partition_field_on_colon(self, line):
        before_colon = []
        after_colon = []
        colon = ''
        found_colon = False
        for i, source in enumerate(_xref_regex.split(line)):
            if found_colon:
                after_colon.append(source)
            else:
                if (i % 2) == 0 and ":" in source:
                    found_colon = True
                    before, colon, after = source.partition(":")
                    before_colon.append(before)
                    after_colon.append(after)
                else:
                    before_colon.append(source)

        return ("".join(before_colon).strip(),
                colon,
                "".join(after_colon).strip())

    def _strip_empty(self, lines):
        if lines:
            start = -1
            for i, line in enumerate(lines):
                if line:
                    start = i
                    break
            if start == -1:
                lines = []
            end = -1
            for i in reversed(range(len(lines))):
                line = lines[i]
                if line:
                    end = i
                    break
            if start > 0 or end + 1 < len(lines):
                lines = lines[start:end + 1]
        return lines


class NumpyDocstring(GoogleDocstring):
    """Convert NumPy style docstrings to reStructuredText.

    Parameters
    ----------
    docstring : str or List[str]
        The docstring to parse, given either as a string or split into
        individual lines.
    config : Optional[sphinx.ext.napoleon.Config or sphinx.config.Config]
        The configuration settings to use. If not given, defaults to the
        config object on `app`; or if `app` is not given defaults to the
        a new `sphinx.ext.napoleon.Config` object.

        See Also
        --------
        :class:`sphinx.ext.napoleon.Config`

    Other Parameters
    ----------------
    app : Optional[sphinx.application.Sphinx]
        Application object representing the Sphinx process.
    what : Optional[str]
        A string specifying the type of the object to which the docstring
        belongs. Valid values: "module", "class", "exception", "function",
        "method", "attribute".
    name : Optional[str]
        The fully qualified name of the object.
    obj : module, class, exception, function, method, or attribute
        The object to which the docstring belongs.
    options : Optional[sphinx.ext.autodoc.Options]
        The options given to the directive: an object with attributes
        inherited_members, undoc_members, show_inheritance and noindex that
        are True if the flag option of same name was given to the auto
        directive.

    Example
    -------
    >>> from sphinx.ext.napoleon import Config
    >>> config = Config(napoleon_use_param=True, napoleon_use_rtype=True)
    >>> docstring = '''One line summary.
    ...
    ... Extended description.
    ...
    ... Parameters
    ... ----------
    ... arg1 : int
    ...     Description of `arg1`
    ... arg2 : str
    ...     Description of `arg2`
    ... Returns
    ... -------
    ... str
    ...     Description of return value.
    ... '''
    >>> print(NumpyDocstring(docstring, config))
    One line summary.
    <BLANKLINE>
    Extended description.
    <BLANKLINE>
    :param arg1: Description of `arg1`
    :type arg1: int
    :param arg2: Description of `arg2`
    :type arg2: str
    <BLANKLINE>
    :returns: Description of return value.
    :rtype: str
    <BLANKLINE>

    Methods
    -------
    __str__()
        Return the parsed docstring in reStructuredText format.

        Returns
        -------
        str
            UTF-8 encoded version of the docstring.

    __unicode__()
        Return the parsed docstring in reStructuredText format.

        Returns
        -------
        unicode
            Unicode version of the docstring.

    lines()
        Return the parsed lines of the docstring in reStructuredText format.

        Returns
        -------
        List[str]
            The lines of the docstring in a list.

    """
    _directive_sections = ['.. index::']

    def _consume_field(self, parse_type=True, prefer_type=False):
        line = next(self._line_iter)
        if parse_type:
            _name, _, _type = self._partition_field_on_colon(line)
        else:
            _name, _type = line, ''
        _name, _type = _name.strip(), _type.strip()
        _name = self._escape_args_and_kwargs(_name)

        if prefer_type and not _type:
            _type, _name = _name, _type
        indent = self._get_indent(line) + 1
        self._consume_indented_block(indent)
        return _name, _type

    def _consume_returns_section(self):
        return self._consume_fields(prefer_type=True)

    def _consume_section_header(self):
        section = next(self._line_iter)
        if not _directive_regex.match(section):
            # Consume the header underline
            next(self._line_iter)
        return section

    def _is_section_break(self):
        line1, line2 = self._line_iter.peek(2)
        return (not self._line_iter.has_next() or
                self._is_section_header() or
                ['', ''] == [line1, line2] or
                (self._is_in_section and
                    line1 and
                    not self._is_indented(line1, self._section_indent)))

    def _is_section_header(self):
        section, underline = self._line_iter.peek(2)
        section = section.lower()
        if section in self._sections and isinstance(underline, string_types):
            return bool(_numpy_section_regex.match(underline))
        elif self._directive_sections:
            if _directive_regex.match(section):
                for directive_section in self._directive_sections:
                    if section.startswith(directive_section):
                        return True
        return False

    _name_rgx = re.compile(r"^\s*(:(?P<role>\w+):`(?P<name>[a-zA-Z0-9_.-]+)`|"
                           r" (?P<name2>[a-zA-Z0-9_.-]+))\s*", re.X)
