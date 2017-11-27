
=======
Doc 484
=======

**PEP 484 type annotations from docstrings****


``doc484`` provides a script to convert PEP484 docstrings to type comments, and can also be used as a normal python module.  It supports the three major docstring conventions:
- `numpy <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy>`_
- `google <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_
- `restructuredText <https://thomas-cokelaer.info/tutorials/sphinx/docstring_python.html#template-py-source-file>`_

Regardless of docstring convention you choose, the types declared within your docstrings should following the guidelines in `PEP 484 <https://www.python.org/dev/peps/pep-0484/>`_, especially use of the `typing <https://docs.python.org/3/library/typing.html>`_ module, where necessary.


Example
=======

Before
------

.. code:: python

    from typing import Optional

    def maxlines(input, numlines=None):
        """
        Parameters
        ----------
        input : str
        numlines : Optional[int]

        Returns
        -------
        str
        """
        if numlines is None:
            return input
        return '\n'.join(input.split('\n')[:numlines])


After
-----

.. code:: python

    from typing import Optional

    def maxlines(input, numlines=None):
        # type: (str, Optional[int]) -> str
        """
        Parameters
        ----------
        input : str
        numlines : Optional[int]

        Returns
        -------
        str
        """
        if numlines is None:
            return input
        return '\n'.join(input.split('\n')[:numlines])


The file is now properly inspectable by mypy or PyCharm.

Installing
----------

.. code::

    pip install doc484


Processing Files
----------------

.. code::
    doc484 -h


TODO
----
- automatically insert `typing` imports
- convert docstrings to function annotations (for python 3.5+)
- add argument for docstring format (or read from setup.cfg)

Also
----

This repo also contains a `mypy <http://mypy.readthedocs.io/en/latest/>`_ plugin that allows type annotations to be read directly from docstrings, but I've given up on that project, due to lack of interest from the `mypy` developers. Here's the `PR <https://github.com/python/mypy/pull/3225>`_, in case it is of any interest.