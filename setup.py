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
    version="0.1.0",
    author="Chad Dombrova",
    description="Generate PEP 484 type comments from docstrings",
    license="MIT",
    keywords=["mypy", "typing", "pep484", "docstrings"],
    url="https://github.com/chadrik/doc484",
    packages=find_packages(),
    entry_points={
        'console_scripts': ['doc484=doc484.__main__:main'],
    },
    install_requires=requirements
)
