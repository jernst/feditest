"""
Generic UBOS Gears Driver
"""
from typing import override

from feditest import nodedriver
from feditest.nodedrivers.ubos_admin import CONTEXT_PAR, UbosAdminNode, UbosAdminNodeConfiguration, UbosAdminNodeDriver
from feditest.nodedrivers import APP_PAR, AccountManager, DefaultAccountManager, NodeConfiguration
from feditest.testplan import TestPlanConstellationNode

@nodedriver
class GenericUbosAdminNodeDriver(UbosAdminNodeDriver):
    @override
    def _instantiate_ubos_node(self, rolename: str, config: UbosAdminNodeConfiguration, account_manager: AccountManager) -> UbosAdminNode:
        return  UbosAdminNode(rolename, config, account_manager)


    @override
    def create_configuration_account_manager(self, rolename: str, test_plan_node: TestPlanConstellationNode) -> tuple[NodeConfiguration, AccountManager | None]:
        # appid = test_plan_node.parameter_or_raise(APPID_PAR)
        appid = test_plan_node.parameter_or_raise(APP_PAR)
        context = test_plan_node.parameter(CONTEXT_PAR) or ''

        return (
            UbosAdminNodeConfiguration.create_from_node_in_testplan(
                    test_plan_node,
                    self,
                    {
                        "appid" : appid,
                        "context" : context
                    } ),
            DefaultAccountManager()
        )
