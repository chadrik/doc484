from __future__ import absolute_import, print_function

from collections import namedtuple

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import *

    Arg = NamedTuple('Arg', [
        ('type', Optional[str]),
        ('line', int),
    ])
else:
    Arg = namedtuple('Arg', ['type', 'line'])
