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

from six import string_types
from six.moves import range

from typing import *

SENTINEL = (None, None)

Arg = NamedTuple('Arg', [
    ('type', str),
    ('line', int),
])

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
    def __init__(self, obj, sentitnel=None):
        """__init__(o, sentinel=None)"""
        self._iterable = iter(obj)
        self._cache = collections.deque()
        if sentitnel is not None:
            self.sentinel = sentitnel
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
    def __init__(self, obj, sentinel=None, modifier=None):
        """__init__(o, sentinel=None, modifier=lambda x: x)"""
        self.modifier = modifier if modifier is not None else lambda x: x
        if not callable(self.modifier):
            raise TypeError('modify_iter(o, modifier): '
                            'modifier must be callable')
        super(modify_iter, self).__init__(obj, sentinel)

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


class GoogleDocstring(object):

    _directive_sections = []

    def __init__(self, docstring, config=None):

        if isinstance(docstring, string_types):
            docstring = docstring.splitlines()
        self._lineno = 1
        self._lines = docstring

        def next_line(line):
            self._lineno += 1
            return line.rstrip(), self._lineno

        self._line_iter = modify_iter(docstring, SENTINEL, modifier=next_line)
        self._is_in_section = False
        self._section_indent = 0

        self._params = None  # type: Optional[List[Tuple[str, Arg]]]
        self._returns = None  # type: Optional[List[Arg]]
        self._yields = None  # type: Optional[List[Arg]]

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

    def _consume_indented_block(self, indent=1):
        # type: () -> List[Tuple[str, int]]
        lines = []  # type: List[Tuple[str, int]]
        line = self._line_iter.peek()
        while(not self._is_section_break() and
              (not line[0] or self._is_indented(line[0], indent))):
            lines.append(next(self._line_iter))
            line = self._line_iter.peek()
        return lines

    def _consume_contiguous(self):
        # type: () -> List[Tuple[str, int]]
        lines = []  # type: List[Tuple[str, int]]
        while (self._line_iter.has_next() and
               self._line_iter.peek() and
               not self._is_section_header()):
            lines.append(next(self._line_iter))
        return lines

    def _consume_empty(self):
        # type: () -> List[Tuple[str, int]]
        lines = []  # type: List[Tuple[str, int]]
        line = self._line_iter.peek()
        while self._line_iter.has_next() and not line[0]:
            lines.append(next(self._line_iter))
            line = self._line_iter.peek()
        return lines

    def _consume_field(self, parse_type=True, prefer_type=False):
        line, lineno = next(self._line_iter)

        before, colon, after = self._partition_field_on_colon(line, lineno)
        _name = before
        _type = ''

        if parse_type:
            match = _google_typed_arg_regex.match(before)
            if match:
                _name = match.group(1)
                _type = match.group(2)

        _name = self._escape_args_and_kwargs(_name)

        if prefer_type and not _type:
            _type, _name = _name, _type
        indent = self._get_indent(line[0]) + 1
        self._consume_indented_block(indent)
        return _name, _type, lineno

    def _consume_fields(self, parse_type=True, prefer_type=False):
        # type: (bool, bool) -> List[Tuple[str, Arg]]
        self._consume_empty()
        fields = []
        while not self._is_section_break():
            _name, _type, lineno = self._consume_field(parse_type, prefer_type)
            if _name or _type:
                fields.append((_name, Arg(_type, lineno)))
        return fields

    def _consume_returns_section(self):
        # type: () -> List[Arg]
        lines = self._dedent(self._consume_to_next_section())
        if lines:
            line, lineno = lines[0]
            before, colon, after = self._partition_field_on_colon(line, lineno)
            _name, _type = '', ''

            if colon:
                match = _google_typed_arg_regex.match(before)
                if match:
                    _type = match.group(2)
                else:
                    _type = before

            return [Arg(_type, lineno)]
        else:
            return []

    def _consume_section_header(self):
        section, _ = next(self._line_iter)
        stripped_section = section.strip(':')
        if stripped_section.lower() in self._sections:
            section = stripped_section
        return section

    def _consume_to_end(self):
        # type: () -> List[Tuple[str, int]]
        lines = []  # type: List[Tuple[str, int]]
        while self._line_iter.has_next():
            lines.append(next(self._line_iter))
        return lines

    def _consume_to_next_section(self):
        # type: () -> List[Tuple[str, int]]
        lines = []  # type: List[Tuple[str, int]]
        self._consume_empty()
        while not self._is_section_break():
            lines.append(next(self._line_iter))
        return lines + self._consume_empty()

    def _dedent(self, lines, full=False):
        # type: (List[Tuple[str, int]], bool) -> List[Tuple[str, int]]
        if full:
            return [(line.lstrip(), lineno) for line, lineno in lines]
        else:
            min_indent = self._get_min_indent(lines)
            return [(line[min_indent:], lineno) for line, lineno in lines]

    def _escape_args_and_kwargs(self, name):
        if name[:2] == '**':
            return r'\*\*' + name[2:]
        elif name[:1] == '*':
            return r'\*' + name[1:]
        else:
            return name

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
        # type: (List[Tuple[str, int]]) -> int
        min_indent = None
        for line, _ in lines:
            if line:
                indent = self._get_indent(line)
                if min_indent is None:
                    min_indent = indent
                elif indent < min_indent:
                    min_indent = indent
        return min_indent or 0

    def _is_indented(self, line, indent=1):
        for i, s in enumerate(line):
            if i >= indent:
                return True
            elif not s.isspace():
                return False
        return False

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
                    not self._is_indented(line[0], self._section_indent)))

    def parse(self):
        self._consume_empty()

        while self._line_iter.has_next():
            if self._is_section_header():
                try:
                    section = self._consume_section_header()
                    self._is_in_section = True
                    self._section_indent = self._get_current_indent()
                    if _directive_regex.match(section):
                        self._consume_to_next_section()
                    else:
                        self._sections[section.lower()]()
                finally:
                    self._is_in_section = False
                    self._section_indent = 0
            else:
                # FIXME: behavior varied based on parsed lines, which we removed
                # if not self._parsed_lines:
                #     self._consume_contiguous() + self._consume_empty()
                # else:
                self._consume_to_next_section()

        return self._params, self._returns, self._yields

    def _skip_section(self):
        self._consume_to_next_section()

    def _parse_parameters_section(self):
        self._params = self._consume_fields()

    def _parse_returns_section(self):
        self._returns = self._consume_returns_section()

    def _parse_yields_section(self):
        self._yields = self._consume_returns_section()

    def _partition_field_on_colon(self, line, lineno):
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


class NumpyDocstring(GoogleDocstring):

    _directive_sections = ['.. index::']

    def _consume_field(self, parse_type=True, prefer_type=False):
        line, lineno = next(self._line_iter)
        if parse_type:
            _name, _, _type = self._partition_field_on_colon(line, lineno)
        else:
            _name = line
            _type = ''
        _name, _type = _name.strip(), _type.strip()
        _name = self._escape_args_and_kwargs(_name)

        if prefer_type and not _type:
            _type, _name = _name, _type
        indent = self._get_indent(line) + 1
        self._consume_indented_block(indent)
        return _name, _type, lineno

    def _consume_returns_section(self):
        # type: () -> List[Arg]
        return [x[1] for x in self._consume_fields(prefer_type=True)]

    def _consume_section_header(self):
        section, _ = next(self._line_iter)
        if not _directive_regex.match(section):
            # Consume the header underline
            next(self._line_iter)
        return section

    def _is_section_break(self):
        line1, line2 = self._line_iter.peek(2)
        return (not self._line_iter.has_next() or
                self._is_section_header() or
                ['', ''] == [line1[0], line2[0]] or
                (self._is_in_section and
                    line1 and
                    not self._is_indented(line1[0], self._section_indent)))

    def _is_section_header(self):
        section, underline = self._line_iter.peek(2)
        section = section[0].lower()
        underline = underline[0]
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
