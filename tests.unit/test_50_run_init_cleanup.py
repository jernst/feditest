"""
Test that @init- and @cleanup-decorated methods are invoked before the first @step and
after the last @step, respectively.
"""

import pytest

import feditest
from feditest import assert_that, cleanup, init, step, test
from feditest.testplan import TestPlan, TestPlanConstellation, TestPlanSessionTemplate, TestPlanTestSpec
from feditest.testrun import TestRun
from feditest.testruncontroller import AutomaticTestRunController


# Records the order in which @init, @step and @cleanup methods actually ran.
# Reset in the init_tests fixture below and inspected by test_run_testplan().
invocation_log: list[str] = []


@pytest.fixture(scope="module", autouse=True)
def init_node_drivers() -> None:
    """
    Cleanly define the NodeDrivers.
    """
    feditest.all_node_drivers = {}
    feditest.dont_load_default_node_drivers()


@pytest.fixture(scope="module", autouse=True)
def init_tests() -> None:
    """
    Cleanly define some tests.
    """
    feditest.all_tests = {}
    feditest._registered_as_test = {}
    feditest._registered_as_test_step = {}
    feditest._loading_tests = True

    invocation_log.clear()

    ##
    ## FediTest tests start here
    ##

    @test
    class AllStepsPass:
        """
        A test class all of whose steps pass. @init must run before step1, and
        @cleanup must run after step2.
        """
        def __init__(self) -> None:
            pass


        @init
        def init_hook(self) -> None:
            invocation_log.append('AllStepsPass.init')


        @step
        def step1(self) -> None:
            invocation_log.append('AllStepsPass.step1')


        @step
        def step2(self) -> None:
            invocation_log.append('AllStepsPass.step2')


        @cleanup
        def cleanup_hook(self) -> None:
            invocation_log.append('AllStepsPass.cleanup')


    @test
    class StepFails:
        """
        A test class one of whose steps fails. @init must still run before step1, and
        @cleanup must still run after the last step, even though step2 failed.
        """
        def __init__(self) -> None:
            pass


        @init
        def init_hook(self) -> None:
            invocation_log.append('StepFails.init')


        @step
        def step1(self) -> None:
            invocation_log.append('StepFails.step1')


        @step
        def step2_fails(self) -> None:
            invocation_log.append('StepFails.step2_fails')
            assert_that(False, 'This step deliberately fails.')


        @step
        def step3(self) -> None:
            invocation_log.append('StepFails.step3')


        @cleanup
        def cleanup_hook(self) -> None:
            invocation_log.append('StepFails.cleanup')

    ##
    ## FediTest tests end here
    ## (Don't forget the next two lines)
    ##

    feditest._loading_tests = False
    feditest._load_tests_pass2()


@pytest.fixture(autouse=True)
def test_plan_fixture() -> TestPlan:
    """
    The test plan tests all known tests.
    """
    constellation = TestPlanConstellation({}, 'No nodes needed')
    tests = [ TestPlanTestSpec(name) for name in sorted(feditest.all_tests.keys()) if feditest.all_tests.get(name) is not None ]
    session = TestPlanSessionTemplate(tests, "Test that @init/@cleanup run before/after @steps")
    ret = TestPlan(session, [ constellation ])
    ret.properties_validate()
    return ret


def test_run_testplan(test_plan_fixture: TestPlan) -> None:
    test_plan_fixture.check_can_be_executed()

    test_run = TestRun(test_plan_fixture)
    controller = AutomaticTestRunController(test_run)
    test_run.run(controller)

    transcript = test_run.transcribe()
    summary = transcript.build_summary()

    assert summary.n_total == 2
    assert summary.n_failed == 1
    assert summary.n_skipped == 0
    assert summary.n_errored == 0
    assert summary.n_passed == 1

    # AllStepsPass sorts before StepFails alphabetically, so run_tests[0] is AllStepsPass.
    assert len(transcript.sessions) == 1
    assert len(transcript.sessions[0].run_tests) == 2

    # @init ran exactly once, before any @step; @cleanup ran exactly once, after all @steps --
    # for both the test that passed and the test that had a failing step.
    assert invocation_log == [
        'AllStepsPass.init',
        'AllStepsPass.step1',
        'AllStepsPass.step2',
        'AllStepsPass.cleanup',
        'StepFails.init',
        'StepFails.step1',
        'StepFails.step2_fails',
        'StepFails.step3',
        'StepFails.cleanup',
    ]
