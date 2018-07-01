from __future__ import absolute_import, print_function

import pytest
from lib2to3.refactor import RefactoringTool, get_fixers_from_package
from doc484.__main__ import main


def convert_string(input):
    tool = RefactoringTool(get_fixers_from_package("doc484.fixes"))
    tree = tool.refactor_string(input, '<test.py>')
    return str(tree)


@pytest.mark.parametrize("config", ['test1', 'test2'])
@pytest.mark.parametrize("format", ['numpydoc', 'googledoc', 'restdoc'])
def test_cli(format, config, pytestconfig, tmpdir):
    fixturedir = pytestconfig.rootdir.join('tests', 'fixtures')

    configdir = fixturedir.join('configs', config)
    results = fixturedir.join('results', '%s.%s.py' % (format, config))
    source = fixturedir.join('formats', (format + '.py'))
    # change directory so we can control discovery of setup.cfg
    configdir.chdir()
    dest = tmpdir.join((format + '.py'))

    errors = main(["--write", "--output-dir", str(tmpdir), str(source)])

    assert errors == []

    with dest.open() as f:
        destlines = f.read()

    if results.exists():
        with results.open() as f:
            expectedlines = f.read()
    else:
        print(destlines)
        expectedlines = ''

    assert expectedlines == destlines
