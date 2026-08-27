"""
A NodeDriver that supports all protocols but doesn't automate anything.
"""

from typing import override

from feditest import nodedriver
from feditest.nodedrivers import AccountManager, Node, NodeConfiguration
from feditest.nodedrivers.fediverse.fallback import AbstractFallbackFediverseNodeDriver, FallbackFediverseNode
from feditest.protocols.fediverse import FediverseNode
from feditest.utils import prompt_user


@nodedriver
class FediverseManualNodeDriver(AbstractFallbackFediverseNodeDriver):
    """
    A NodeDriver that supports all web server-side protocols but doesn't automate anything.
    """
    @override
    def _provision_node(self, rolename: str, config: NodeConfiguration, account_manager: AccountManager | None) -> FediverseNode:
        prompt_user(
                f'Manually provision the Node for constellation role { rolename }'
                + f' at host { config.hostname } with app { config.app } and hit return when done: ')
        return FallbackFediverseNode(rolename, config, account_manager)


    @override
    def _unprovision_node(self, node: Node) -> None:
        prompt_user(f'Manually unprovision the Node for constellation role { node.rolename } and hit return when done: ')
