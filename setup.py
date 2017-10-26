from setuptools import setup, find_packages
import os.path

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with open(os.path.join(HERE, *parts)) as f:
        return f.read()


requirements = [x.strip() for x in read('requirements.txt').split('\n')
                if x.strip()]

setup(
    name="doc484",
    version="0.0.2",
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
        'console_scripts': ['doc484=doc484.__main__:main'],
    },
    install_requires=requirements
)
