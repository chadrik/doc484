
=======
Doc 484
=======

PEP 484 type annotations from docstrings
========================================

``doc484`` provides a script to convert PEP484 docstrings to type comments, and can also be used as a normal python module.  It supports the three major docstring conventions `numpy <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy>`_, `google <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_, and `restructuredText <https://thomas-cokelaer.info/tutorials/sphinx/docstring_python.html#template-py-source-file>`_

Regardless of docstring convention you choose, the types declared within your docstrings should following the guidelines in `PEP 484 <https://www.python.org/dev/peps/pep-0484/>`_, especially use of the `typing <https://docs.python.org/3/library/typing.html>`_ module, where necessary.

Why Use This?
=============

If you answer affirmative to at least 2 of these, this project may be for you:

- You're stuck supporting python 2.x, so you have to use type comments, which are much harder to visually grok
- Your projects have existing docstrings with types that are already mostly correct
- You find it easier to maintain and comprehend types specified alongside the description of an argument

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
==========

.. code::

    pip install doc484


Usage
=====

.. code::
    doc484 -h


TODO
====
- automatically insert `typing` imports
- convert docstrings to function annotations (for python 3.5+)
- add argument for docstring format (or read from setup.cfg)
