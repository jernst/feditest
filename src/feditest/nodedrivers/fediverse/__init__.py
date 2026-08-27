"""
"""

from typing import override

from feditest import nodedriver
from feditest.nodedrivers import AccountManager, NodeConfiguration
from feditest.nodedrivers.fediverse.fallback import AbstractFallbackFediverseNodeDriver, FallbackFediverseNode


@nodedriver
class FediverseSaasNodeDriver(AbstractFallbackFediverseNodeDriver):
    """
    A NodeDriver that supports all protocols but doesn't automate anything and assumes the
    Node under test exists as a website that we don't have/can provision/unprovision.
    """
    @override
    def _provision_node(self, rolename: str, config: NodeConfiguration, account_manager: AccountManager | None) -> FallbackFediverseNode:
        return FallbackFediverseNode(rolename, config, account_manager)


    # No need to override _unprovision_node()

