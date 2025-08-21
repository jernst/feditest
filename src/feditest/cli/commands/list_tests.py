"""
List the available tests
"""

from argparse import ArgumentParser, Namespace, _SubParsersAction
import re

import feditest
from feditest.cli.utils import (
    add_filter_regex_argument,
    add_testsdir_argument
)


def run(parser: ArgumentParser, args: Namespace, remaining: list[str]) -> int:
    """
    Run this command.
    """
    if len(remaining):
        parser.print_help()
        return 0

    pattern = re.compile(args.filter_regex) if args.filter_regex else None

    feditest.load_default_tests()
    feditest.load_tests_from(args.testsdir)

    for name in sorted(feditest.all_tests.keys()):
        if pattern is None or pattern.match(name):
            print(name)

    return 0


def add_sub_parser(parent_parser: _SubParsersAction, cmd_name: str) -> ArgumentParser:
    """
    Add command-line options for this sub-command
    parent_parser: the parent argparse parser
    cmd_name: name of this command
    """
    parser = parent_parser.add_parser(cmd_name, help='List the available tests')
    add_filter_regex_argument(parser)
    add_testsdir_argument(parser)

    return parser
