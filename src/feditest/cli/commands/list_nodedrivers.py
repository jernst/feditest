"""
List the available drivers for nodes that can be tested
"""

from argparse import ArgumentParser, Namespace, _SubParsersAction

import feditest
import feditest.cli
from feditest.cli.utils import add_nodedriversdir_argument


def run(parser: ArgumentParser, args: Namespace, remaining: list[str]) -> int:
    """
    Run this command.
    """
    if len(remaining):
        parser.print_help()
        return 0

    feditest.load_default_node_drivers()
    feditest.load_node_drivers_from(args.nodedriversdir)

    for name in sorted(feditest.all_node_drivers.keys()):
        print(name)

    return 0


def add_sub_parser(parent_parser: _SubParsersAction, cmd_name: str) -> ArgumentParser:
    """
    Add command-line options for this sub-command
    parent_parser: the parent argparse parser
    cmd_name: name of this command
    """
    parser = parent_parser.add_parser(cmd_name, help='List the available drivers for nodes that can be tested')
    add_nodedriversdir_argument(parser)

    return parser
