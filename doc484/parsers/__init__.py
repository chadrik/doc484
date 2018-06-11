from __future__ import absolute_import, print_function

from typing import NamedTuple

Arg = NamedTuple('Arg', [
    ('type', str),
    ('line', int),
])
