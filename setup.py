from setuptools import setup, find_packages

setup(
    name="doc484",
    version="0.0.1",
    author="Chad Dombrova",
    description="Utilities for working with PEP484 types within docstrings",
    license="BSD",
    keywords="example documentation tutorial",
    url="http://packages.python.org/an_example_pypi_project",
    packages=find_packages(),
    # long_description=read('README'),
    # classifiers=[
    #     "Development Status :: 3 - Alpha",
    #     "Topic :: Utilities",
    #     "License :: OSI Approved :: BSD License",
    # ],
    entry_points={
        'console_scripts': ['doc484=doc484.__main__'],
    }
)
