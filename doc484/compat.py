from __future__ import absolute_import, print_function

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
    range = range
else:
    string_types = unicode, str
    range = xrange
