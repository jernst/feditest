"""
Create a simple node file
"""

from argparse import ArgumentParser, Namespace, _SubParsersAction
from feditest.testplan import TestPlanConstellationNode


def run(parser: ArgumentParser, args: Namespace, remaining: list[str]) -> int:
    """
    Run this command.
    """

    if remaining:
        parser.print_help()
        return 0

    parameters = None
    if args.parameter:
        parameters = {}
        for pair in args.parameter:
            name, value = pair.split('=')
            parameters[name] = value

    # There isn't really a practical way to also specify accounts and non-existing acccounts.
    # Editing the generated file seems easier.

    node = TestPlanConstellationNode(nodedriver=args.nodedriver, parameters=parameters)

    if args.out:
        node.save(args.out)
    else:
        node.print()

    return 0


def add_sub_parser(parent_parser: _SubParsersAction, cmd_name: str) -> ArgumentParser:
    """
    Add command-line options for this sub-command
    parent_parser: the parent argparse parser
    cmd_name: name of this command
    """
    parser = parent_parser.add_parser(cmd_name, help='Create a basic node file')
    parser.add_argument('--nodedriver', required=True, help='Name of NodeDriver for the node')
    parser.add_argument('--parameter', action='append', required=False,
                        help='Parameters for the node, given as parameterkey=parametervalue')
    parser.add_argument('--out', '-o', default=None, required=False, help='Name of the file for the generated node')

    return parser
