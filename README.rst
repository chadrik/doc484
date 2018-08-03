
=======
Doc 484
=======

.. image:: https://travis-ci.org/chadrik/doc484.svg?branch=master
   :target: https://travis-ci.org/chadrik/doc484
   :alt: CI Status

Generate PEP 484 type annotations from docstrings
=================================================

``doc484`` provides a script to find type declarations within your docstrings and convert them to PEP 484 type comments. It supports the three major docstring conventions `numpy <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_numpy.html#example-numpy>`_, `google <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_, and `restructuredText (sphinx) <https://thomas-cokelaer.info/tutorials/sphinx/docstring_python.html#template-py-source-file>`_

Regardless of docstring convention you choose, the types declared within your docstrings should following the guidelines in `PEP 484 <https://www.python.org/dev/peps/pep-0484/>`_, especially use of the `typing <https://docs.python.org/3/library/typing.html>`_ module, where necessary.

Why Use This?
=============

If you answer affirmative to at least 2 of these, this project is probably for you:

- You're stuck supporting python 2.7, so you have to use type comments, which are far less comprehensible than the type annotations supported in 3.5+
- Your projects have existing docstrings with types that are already mostly correct
- You find it easier to maintain and comprehend types specified alongside the description of an argument

Examples
========

Basic
~~~~~

Before
------

.. code:: python

    from typing import Optional

    def maxlines(input, numlines=None):
        """
        Trim a string to a maximum number of lines.

        Parameters
        ----------
        input : str
        numlines : Optional[int]
            maximum number of lines

        Returns
        -------
        str
        """
        if numlines is None:
            return input
        return '\n'.join(input.split('\n')[:numlines])


After
-----

After running `doc484`:

.. code:: python

    from typing import Optional

    def maxlines(input, numlines=None):
        # type: (str, Optional[int]) -> str
        """
        Trim a string to a maximum number of lines.

        Parameters
        ----------
        input : str
        numlines : Optional[int]
            maximum number of lines

        Returns
        -------
        str
        """
        if numlines is None:
            return input
        return '\n'.join(input.split('\n')[:numlines])


The file is now properly inspectable by mypy or PyCharm.

Advanced
~~~~~~~~

A more complex example demonstrates some of the added readability that comes from specifying types within your docstrings.
Below we use numpy format to document a generator of tuples:

Before
------

.. code:: python

    from typing import *

    def itercount(input, char):
        """
        Iterate over input strings and yield a tuple of the string with `char`
        removed, and the number of occurrences of `char`.

        Parameters
        ----------
        input : Iterable[str]
        char : str
            character to remove and count

        Yields
        ------
        stripped : str
            input string with all occurrences of `char` removed
        count : int
            number of occurrences of `char`
        """
        for x in input:
            yield x.strip(char), x.count(char)


After
-----

.. code:: python

    from typing import *

    def itercount(input, char):
        # type: (Iterable[str], str) -> Iterator[Tuple[str, int]]
        """
        Iterate over input strings and yield a tuple of the string with `char`
        removed, and the number of occurrences of `char`.

        Parameters
        ----------
        input : Iterable[str]
        char : str
            character to remove and count

        Yields
        ------
        stripped : str
            input string with all occurrences of `char` removed
        count : int
            number of occurrences of `char`
        """
        for x in input:
            yield x.strip(char), x.count(char)

Installing
==========

.. code::

    pip install doc484


Usage
=====

.. code::

    doc484 -h

By default ``doc484`` will not modify files, instead it will print out a diff of what would be modified.  When you're ready to make changes, add the `--write` flag.

Check the scripts directory for an example of how to automatically run ``doc484`` on modified files in your git or mercurial repository.


Configuration
=============

You can override any of the command line options using an ini-style configuration file.
By default, ``doc484`` looks for a setup.cfg file in the current working directory, but you can also provide a config explicitly using the ``--config`` option.

For example, to override the number of processes to use when converting, and specify the docstring format for the project, add this to your setup.cfg and run `doc484` from the directory where this config file resides:

.. code:: ini

   [doc484]
   processes = 12
   format = numpy

TODO
====

- automatically insert ``typing`` imports
- add option to convert docstrings to function annotations (for python 3.5+)
- complete support for fixing non-PEP484-compliant docstrings (e.g. ``list of str``)
- convert ``doctypes`` utility script to python?
