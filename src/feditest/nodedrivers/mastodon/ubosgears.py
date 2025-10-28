"""
"""

import re
import secrets
import string
import subprocess
from typing import cast

from feditest import nodedriver
from feditest.nodedrivers import (
    Account,
    NonExistingAccount,
    AccountManager,
    DefaultAccountManager,
    Node,
    NodeConfiguration
)
from feditest.nodedrivers.mastodon import (
    EMAIL_ACCOUNT_FIELD,
    OAUTH_TOKEN_ACCOUNT_FIELD,
    PASSWORD_ACCOUNT_FIELD,
    MastodonAccount,
    MastodonNode,
    MastodonUserPasswordAccount
)
from feditest.nodedrivers.mastodon.ubosgears_shared import MastodonUbosNodeConfiguration
from feditest.nodedrivers.ubosgears import (
    UbosNode,
    UbosNodeConfiguration,
    UbosNodeDriver
)
from feditest.protocols.fediverse import (
    FediverseNonExistingAccount,
    ROLE_NON_EXISTING_ACCOUNT_FIELD,
    ROLE_ACCOUNT_FIELD,
    USERID_ACCOUNT_FIELD,
    USERID_NON_EXISTING_ACCOUNT_FIELD
)

from feditest.reporting import error, trace
from feditest.testplan import TestPlanConstellationNode, TestPlanNodeAccountField, TestPlanNodeNonExistingAccountField


class MastodonUbosAccountManager(DefaultAccountManager):
    """
    Knows how to provision new accounts in Mastodon
    """
    # Python 3.12 @override
    def set_node(self, node: Node) -> None:
        """
        We override this so we can insert the admin account in the list of accounts, now that the Node has been instantiated.
        """
        super().set_node(node)

        if not self._accounts_allocated_to_role and not self._accounts_not_allocated_to_role:
            config = cast(UbosNodeConfiguration, node.config)
            admin_account = MastodonUserPasswordAccount(None, config.admin_userid, config.admin_credential, config.admin_email)
            admin_account.set_node(node)
            self._accounts_not_allocated_to_role.append(admin_account)


class MastodonUbosNode(MastodonNode, UbosNode):
    """
    A Mastodon Node running on UBOS. This means we know how to interact with it exactly.
    """
    # Python 3.12 @override
    def provision_account_for_role(self, role: str | None = None) -> Account | None:
        trace('Provisioning new user')
        userid = self._generate_candidate_userid()
        useremail = f'{ userid }@localhost' # Mastodon checks that the host exists, so we pick localhost

        result = self._invoke_tootctl(f'accounts create { userid } --email { useremail } --approve --confirmed --role=Owner')

        if result.returncode:
            error(f'Provisioniong new user { userid } on Mastodon Node { self._rolename } failed.')
            return None

        m = re.search( r'password:\s+([a-z0-9]+)', result.stdout )
        if not m:
            error('Failed to parse tootctl accounts create output:' + result.stdout)
            return None

        passwd = m.group(1)
        trace(f'New Mastodon user in role { role } on { self }: userid: "{ userid }", passwd: "{ passwd }", email: "{ useremail }".')
        return MastodonUserPasswordAccount(role, userid, passwd, useremail)


    def provision_non_existing_account_for_role(self, role: str | None = None) -> NonExistingAccount | None:
        # We just make it up
        userid = self._generate_candidate_userid()

        return FediverseNonExistingAccount(role, userid)


    def _generate_candidate_userid(self) -> str:
        """
        Given what we know about Mastodon's userids, generate a random one that might work.
        """
        # Do not use uppercase characters. The Mastodon API will not let you log on.
        chars = string.ascii_lowercase + string.digits
        userid = ''.join(secrets.choice(chars) for i in range(8))
        return userid


    def _invoke_tootctl(self, args: str) -> subprocess.CompletedProcess:
        config = cast(UbosNodeConfiguration, self.config)

        cmd = f'cd /ubos/lib/mastodon/{ config.appconfigid }/mastodon'
        cmd += ' && sudo RAILS_ENV=production bin/tootctl ' # This needs to be run as root, because .env.production is not world-readable
        cmd += args

        node_driver = cast(MastodonUbosNodeDriver, self.node_driver)
        ret = node_driver._exec_shell(cmd, config.rshcmd, capture_output=True)
        return ret


@nodedriver
class MastodonUbosNodeDriver(UbosNodeDriver):
    """
    Knows how to instantiate Mastodon via UBOS.
    """
    # Python 3.12 @override
    @staticmethod
    def test_plan_node_account_fields() -> list[TestPlanNodeAccountField]:
        return [ USERID_ACCOUNT_FIELD, EMAIL_ACCOUNT_FIELD, PASSWORD_ACCOUNT_FIELD, OAUTH_TOKEN_ACCOUNT_FIELD, ROLE_ACCOUNT_FIELD ]


    # Python 3.12 @override
    @staticmethod
    def test_plan_node_non_existing_account_fields() -> list[TestPlanNodeNonExistingAccountField]:
        return [ USERID_NON_EXISTING_ACCOUNT_FIELD, ROLE_NON_EXISTING_ACCOUNT_FIELD ]


    # Python 3.12 @override
    def create_configuration_account_manager(self, rolename: str, test_plan_node: TestPlanConstellationNode) -> tuple[NodeConfiguration, AccountManager | None]:
        accounts : list[Account] = []
        if test_plan_node.accounts:
            for index, account_info in enumerate(test_plan_node.accounts):
                accounts.append(MastodonAccount.create_from_account_info_in_testplan(
                        account_info,
                        f'Constellation role "{ rolename }", NodeDriver "{ self }, Account { index }: '))

        non_existing_accounts : list[NonExistingAccount] = []
        if test_plan_node.non_existing_accounts:
            for index, non_existing_account_info in enumerate(test_plan_node.non_existing_accounts):
                non_existing_accounts.append(FediverseNonExistingAccount.create_from_non_existing_account_info_in_testplan(
                        non_existing_account_info,
                        f'Constellation role "{ rolename }", NodeDriver "{ self }, Non-existing account { index }: '))

        # Once has the Node has been instantiated (we can't do that here yet): if the user did not specify at least one Account, we add the admin account

        return (
            MastodonUbosNodeConfiguration.create_from_node_in_testplan(
                test_plan_node,
                self,
                appconfigjson = {
                    "appid" : "mastodon",
                    "context" : "",
                    "customizationpoints" : {
                        "mastodon" : {
                            "singleusermode" : {
                                "value" : False
                            },
                            "allowed_private_addresses" : {
                                "value" : "192.168.1.1/16" # Allow testing in a Linux container
                            }
                        }
                    }
                },
                defaults = {
                    'app' : 'Mastodon'
                }),
            MastodonUbosAccountManager(accounts, non_existing_accounts)
        )

    # Python 3.12 @override
    def _instantiate_ubos_node(self, rolename: str, config: UbosNodeConfiguration, account_manager: AccountManager) -> Node:
        return MastodonUbosNode(rolename, config, account_manager)
