from setuptools import setup, find_packages
import os.path

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with open(os.path.join(HERE, *parts)) as f:
        return f.read()


setup(
    name="doc484",
    version="0.3.0",
    author="Chad Dombrova",
    description="Generate PEP 484 type comments from docstrings",
    long_description=read("README.rst"),
    license="MIT",
    keywords=["mypy", "typing", "pep484", "docstrings", "annotations"],
    url="https://github.com/chadrik/doc484",
    packages=find_packages(),
    entry_points={
        'console_scripts': ['doc484=doc484.__main__:main'],
    },
    install_requires=[
        "docutils",  # only required for rest format
    ],
    extras_require={
        "tests": [
            "coverage",
            "pytest==3.6.2",
            "tox==2.7.0",
        ],
    },
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
