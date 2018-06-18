from __future__ import absolute_import, print_function

import logging
import optparse
import os
import sys

from lib2to3 import refactor
from lib2to3.main import warn, StdoutRefactoringTool

from doc484.compat import PY3
import doc484.formats

if PY3:
    from configparser import ConfigParser, NoSectionError
else:
    from ConfigParser import SafeConfigParser as ConfigParser, NoSectionError

if False:
    from typing import *

fixer_pkg = 'doc484.fixes'


def apply_config(keys, options, path=None):
    # type: (, optparse.Values, Optional[str]) -> Dict[str, str]
    """
    Read setup.cfg from path or current working directory and apply it to the
    parsed options

    Parameters
    ----------
    keys
    options : optparse.Values
        parsed options
    path : Optional[str]

    Returns
    -------
    Dict[str, str]
        default types by argument name
    """
    if not path:
        path = os.getcwd()

    config_file = os.path.join(path, 'setup.cfg')
    parser = ConfigParser()
    parser.read(config_file)

    def addopt(key, typ, default):
        if hasattr(options, key):
            return

        methname = 'get'
        if typ not in ('string', 'choice'):
            methname += typ

        method = getattr(parser, methname)

        val = method('doc484', key, fallback=default)
        setattr(options, key, val)

    for key, typ, default in keys:
        addopt(key, typ, default)

    try:
        return dict(parser.items('doc484:default_arg_types'))
    except NoSectionError:
        return {}


def _get_options_data(parser):
    defaults = parser.get_default_values().__dict__
    keys = []
    for opt in parser.option_list:
        if opt.dest == 'config':
            continue
        opttype = opt.type
        if opttype is None:
            if opt.action in ['store_true', 'store_false']:
                opttype = 'boolean'
            elif opt.action in ['help', 'append']:
                continue
            else:
                raise TypeError(opt.action)
        keys.append((opt.dest, opttype, defaults[opt.dest]))
    return keys


# copied and modified from lib2to3.main
def main(args=None):
    """Main program.

    Returns a suggested exit status (0, 1, 2).
    """
    # Set up option parser
    parser = optparse.OptionParser(usage="doc484 [options] file|dir ...")
    parser.add_option("-d", "--doctests_only", action="store_true",
                      default=False, help="Fix up doctests only")
    parser.add_option("-f", "--format",
                      choices=list(doc484.formats.format_map.keys()),
                      help="Docstring convention")
    parser.add_option("-j", "--processes", action="store", default=1,
                      type="int", help="Run 2to3 concurrently")
    # parser.add_option("-f", "--fix", action="append", default=[],
    #                   help="Each FIX specifies a transformation; default: all")
    # parser.add_option("-x", "--nofix", action="append", default=[],
    #                   help="Prevent a transformation from being run")
    # parser.add_option("-l", "--list-fixes", action="store_true", default=False,
    #                   help="List available transformations")
    parser.add_option("-p", "--print-function", action="store_true",
                      default=False,
                      help="Modify the grammar so that print() is a function")
    parser.add_option("-v", "--verbose", action="store_true", default=False,
                      help="More verbose logging")
    parser.add_option("--no-diffs", action="store_true", default=False,
                      help="Don't show diffs of the refactoring")
    parser.add_option("-w", "--write", action="store_true", default=False,
                      help="Write back modified files")
    parser.add_option("-n", "--nobackups", action="store_true", default=False,
                      help="Don't write backups for modified files")
    parser.add_option("-c", "--config", action="store", type="str",
                      default=None, help="Read settings from the specified "
                      "ini-style configuration file (defaults to `./setup.cfg'")
    parser.add_option("-o", "--output-dir", action="store", type="str",
                      default="", help="Put output files in this directory "
                      "instead of overwriting the input files.  Requires -n.")
    parser.add_option("-W", "--write-unchanged-files", action="store_true",
                      default=False,
                      help="Also write files even if no changes were required"
                      " (useful with --output-dir); implies -w.")
    parser.add_option("--add-suffix", action="store", type="str", default="",
                      help="Append this string to all output filenames."
                      " Requires -n if non-empty.  "
                      "ex: --add-suffix='3' will generate .py3 files.")

    # Parse command line arguments
    refactor_stdin = False
    flags = {}

    # pass in `values` to prevent defaults from being populated, so that
    # values read from the config file can take precedence over defaults.
    # order of precedence: specified options > config options > parser defaults
    options, args = parser.parse_args(args, values=optparse.Values({}))

    default_arg_types = apply_config(_get_options_data(parser), options,
                                     path=getattr(options, 'config', None))

    doc484.formats.default_arg_types.update(default_arg_types)

    if options.format:
        if options.verbose:
            print("Using %r format" % options.format)
        doc484.formats.set_default_format(options.format)

    if options.write_unchanged_files:
        flags["write_unchanged_files"] = True
        if not options.write:
            warn("--write-unchanged-files/-W implies -w.")
        options.write = True
    # If we allowed these, the original files would be renamed to backup names
    # but not replaced.
    if options.output_dir and not options.nobackups:
        parser.error("Can't use --output-dir/-o without -n.")
    if options.add_suffix and not options.nobackups:
        parser.error("Can't use --add-suffix without -n.")

    if not options.write and options.no_diffs:
        warn("not writing files and not printing diffs; that's not "
             "very useful")
    if not options.write and options.nobackups:
        parser.error("Can't use -n without -w")
    # if options.list_fixes:
    #     print("Available transformations for the -f/--fix option:")
    #     for fixname in refactor.get_all_fix_names(fixer_pkg):
    #         print(fixname)
    #     if not args:
    #         return 0
    if not args:
        print("At least one file or directory argument required.",
              file=sys.stderr)
        print("Use --help to show usage.", file=sys.stderr)
        return 2
    if "-" in args:
        refactor_stdin = True
        if options.write:
            print("Can't write to stdin.", file=sys.stderr)
            return 2
    if options.print_function:
        flags["print_function"] = True

    # Set up logging handler
    level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(format='%(name)s: %(message)s', level=level)
    logger = logging.getLogger('lib2to3.main')

    # NOTE: removing this until we have more fixes
    # Initialize the refactoring tool
    # avail_fixes = set(refactor.get_fixers_from_package(fixer_pkg))
    # unwanted_fixes = set(fixer_pkg + ".fix_" + fix for fix in options.nofix)
    explicit = set()
    # if options.fix:
    #     all_present = False
    #     for fix in options.fix:
    #         if fix == "all":
    #             all_present = True
    #         else:
    #             explicit.add(fixer_pkg + ".fix_" + fix)
    #     requested = avail_fixes.union(explicit) if all_present else explicit
    # else:
    #     requested = avail_fixes.union(explicit)
    # fixer_names = requested.difference(unwanted_fixes)

    fixer_names = {'doc484.fixes.fix_type_comments'}

    input_base_dir = os.path.commonprefix(args)
    if (input_base_dir and not input_base_dir.endswith(os.sep)
        and not os.path.isdir(input_base_dir)):
        # One or more similar names were passed, their directory is the base.
        # os.path.commonprefix() is ignorant of path elements, this corrects
        # for that weird API.
        input_base_dir = os.path.dirname(input_base_dir)
    if options.output_dir:
        input_base_dir = input_base_dir.rstrip(os.sep)
        logger.info('Output in %r will mirror the input directory %r layout.',
                    options.output_dir, input_base_dir)
    rt = StdoutRefactoringTool(
            sorted(fixer_names), flags, sorted(explicit),
            options.nobackups, not options.no_diffs,
            input_base_dir=input_base_dir,
            output_dir=options.output_dir,
            append_suffix=options.add_suffix)

    # Refactor all files and directories passed as arguments
    if not rt.errors:
        if refactor_stdin:
            rt.refactor_stdin()
        else:
            try:
                rt.refactor(args, options.write, options.doctests_only,
                            options.processes)
            except refactor.MultiprocessingUnsupported:
                assert options.processes > 1
                print("Sorry, -j isn't supported on this platform.",
                      file=sys.stderr)
                return 1
        rt.summarize()

    # Return error status (0 if rt.errors is zero)
    return int(bool(rt.errors))


if __name__ == '__main__':
    sys.exit(main())
