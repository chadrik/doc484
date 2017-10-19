from __future__ import absolute_import, print_function

import sys
collect_ignore = []

if sys.version_info[:2] < (3, 5):
    collect_ignore.append("tests/test_mypy_plugin.py")
