"""
Run one or more tests
"""

from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import cast

import feditest
from feditest.cli.utils import (
    DEFAULT_CONSTELLATION_FILE,
    add_filter_regex_argument,
    add_nodedriversdir_argument,
    add_test_argument,
    add_testsdir_argument,
    create_plan_from_session_and_constellations,
    create_plan_from_testplan
)
from feditest.registry import Registry, set_registry_singleton
from feditest.reporting import fatal, warning
from feditest.testplan import TestPlan
from feditest.testrun import TestRun
from feditest.testruncontroller import AutomaticTestRunController, InteractiveTestRunController, TestRunController
from feditest.testruntranscriptserializer.json import JsonTestRunTranscriptSerializer
from feditest.testruntranscriptserializer.html import HtmlRunTranscriptSerializer
from feditest.testruntranscriptserializer.summary import SummaryTestRunTranscriptSerializer
from feditest.testruntranscriptserializer.tap import TapTestRunTranscriptSerializer
from feditest.utils import FEDITEST_VERSION, hostname_validate


def run(parser: ArgumentParser, args: Namespace, remaining: list[str]) -> int:
    """
    Run this command.
    """
    if len(remaining):
        parser.print_help()
        return 0

    feditest.load_node_drivers_from(args.nodedriversdir)

    feditest.load_default_tests()
    feditest.load_tests_from(args.testsdir)

    if args.domain:
        set_registry_singleton(Registry.create(args.domain)) # overwrite

    # Determine testplan. While we are at it, check consistency of arguments.
    plan : TestPlan | None = None
    if args.testplan:
        plan = create_plan_from_testplan(args)
    else:
        plan = create_plan_from_session_and_constellations(args)

    if not plan:
        fatal('Cannot find or create test plan ')
        return 1 # make linter happy

    if not plan.is_compatible_type():
        warning(f'Test plan has unexpected type { plan.type }: incompatibilities may occur.')
    if not plan.has_compatible_version():
        warning(f'Test plan was created by FediTest { plan.feditest_version }, you are running FediTest { FEDITEST_VERSION }: incompatibilities may occur.')
    plan.check_can_be_executed()

    test_run = TestRun(plan, args.who)
    if args.interactive :
        warning('--interactive: implementation is incomplete')
        controller : TestRunController = InteractiveTestRunController(test_run)
    else:
        controller = AutomaticTestRunController(test_run)
    test_run.run(controller)

    transcript : feditest.testruntranscript.TestRunTranscript = test_run.transcribe()

    if isinstance(args.tap, str) or args.tap:
        TapTestRunTranscriptSerializer().write(transcript, cast(str|None, args.tap))

    if isinstance(args.html, str):
        HtmlRunTranscriptSerializer(args.template_path).write(transcript, args.html)
    elif args.html:
        warning('--html requires a filename: skipping')
    elif args.template_path:
        warning('--template-path only supported with --html. Ignoring.')

    if isinstance(args.json, str) or args.json:
        JsonTestRunTranscriptSerializer().write(transcript, args.json)

    if isinstance(args.summary, str) or args.summary:
        SummaryTestRunTranscriptSerializer().write(transcript, args.summary)

    if transcript.build_summary().n_failed > 0:
        print('FAILED.')
        return 1
    return 0


def add_sub_parser(parent_parser: _SubParsersAction, cmd_name: str) -> ArgumentParser:
    """
    Add command-line options for this sub-command
    parent_parser: the parent argparse parser
    cmd_name: name of this command
    """
    # general flags and options
    parser = parent_parser.add_parser(cmd_name, help='Run one or more tests' )
    add_nodedriversdir_argument(parser)
    add_testsdir_argument(parser)
    parser.add_argument('--domain', type=hostname_validate, help='Local-only DNS domain for the DNS hostnames that are auto-generated for nodes')
    parser.add_argument('-i', '--interactive', action="store_true", help="Run the tests interactively")
    parser.add_argument('--who', action='store_true', help="Record who ran the test plan on what host.")

    # test plan options. We do not use argparse groups, as the situation is more complicated than argparse seems to support
    parser.add_argument('--name', default=None, required=False, help='Name of the generated test plan')
    parser.add_argument('--testplan', help='Name of the file that contains the test plan to run')
    parser.add_argument('--constellation', action='append', help=f'File(s) each containing a JSON fragment defining a constellation. Fallback default is { DEFAULT_CONSTELLATION_FILE }')
    parser.add_argument('--session', '--session-template', required=False, help='File(s) each containing a JSON fragment defining a test session')
    parser.add_argument('--node', action='append',
                        help="Use <role>=<file> to specify that the node definition in 'file' is supposed to be used for constellation role 'role'")
    add_filter_regex_argument(parser)
    add_test_argument(parser)

    # output options
    parser.add_argument('--tap', nargs="?", const=True, default=False,
                        help="Write results in TAP format to stdout, or to the provided file (if given).")
    html_group = parser.add_argument_group('html', 'HTML options')
    html_group.add_argument('--html',
                        help="Write results in HTML format to the provided file.")
    html_group.add_argument('--template-path', required=False,
                        help="When specifying --html, use this template path override (comma separated directory names)")
    parser.add_argument('--json', '--testresult', nargs="?", const=True, default=False,
                        help="Write results in JSON format to stdout, or to the provided file (if given).")
    parser.add_argument('--summary', nargs="?", const=True, default=False,
                        help="Write summary to stdout, or to the provided file (if given). This is the default if no other output option is given")

    return parser
