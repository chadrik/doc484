
## Utilities for using PEP484 type annotations within docstrings

This is still a very rough draft.

It is currently comprised of two tools:
- a script to convert PEP484 docstrings to type comments
- a [mypy](http://mypy.readthedocs.io/en/latest/) plugin that enables it to read type annotations from docstrings.  

Supports numpy, google, and restructuredText (aka sphinx) styled docstrings.


### mypy plugin

To use the plugin:

```
git clone https://github.com/chadrik/mypy
cd mypy
git checkout docstrings
python3 -m pip install -r requirements.txt
python3 -m mypy /path/to/file
```

### docs-to-comments converter

To use the converter:

```
pip install -r requirements.txt
python ./docs-to-comments.py /path/to/file
```
