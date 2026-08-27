"""
"""

from typing import cast, override

from feditest import nodedriver
from feditest.nodedrivers import (
    Account,
    AccountManager,
    DefaultAccountManager,
    NodeConfiguration,
    NodeDriver,
    NonExistingAccount,
    APP_PAR,
    APP_VERSION_PAR,
    HOSTNAME_PAR
)
from feditest.nodedrivers.mastodon import (
    EMAIL_ACCOUNT_FIELD,
    OAUTH_TOKEN_ACCOUNT_FIELD,
    PASSWORD_ACCOUNT_FIELD,
    VERIFY_API_TLS_CERTIFICATE_PAR,
    MastodonAccount,
    MastodonNode,
    NodeWithMastodonApiConfiguration
)
from feditest.protocols.fediverse import (
    ROLE_ACCOUNT_FIELD,
    ROLE_NON_EXISTING_ACCOUNT_FIELD,
    USERID_ACCOUNT_FIELD,
    USERID_NON_EXISTING_ACCOUNT_FIELD,
    FediverseNode,
    FediverseNonExistingAccount
)
from feditest.testplan import (
    TestPlanConstellationNode,
    TestPlanNodeAccountField,
    TestPlanNodeNonExistingAccountField,
    TestPlanNodeParameter
)
from feditest.utils import (
    hostname_validate,
    prompt_user_parse_validate
)


@nodedriver
class MastodonSaasNodeDriver(NodeDriver):
    """
    Connect to an existing hosted instance of Mastodon.
    """
    @override
    @staticmethod
    def test_plan_node_parameters() -> list[TestPlanNodeParameter]:
        return [ APP_PAR, APP_VERSION_PAR, HOSTNAME_PAR, VERIFY_API_TLS_CERTIFICATE_PAR ]


    @override
    @staticmethod
    def test_plan_node_account_fields() -> list[TestPlanNodeAccountField]:
        return [ USERID_ACCOUNT_FIELD, EMAIL_ACCOUNT_FIELD, PASSWORD_ACCOUNT_FIELD, OAUTH_TOKEN_ACCOUNT_FIELD, ROLE_ACCOUNT_FIELD ]


    @override
    @staticmethod
    def test_plan_node_non_existing_account_fields() -> list[TestPlanNodeNonExistingAccountField]:
        return [ USERID_NON_EXISTING_ACCOUNT_FIELD, ROLE_NON_EXISTING_ACCOUNT_FIELD ]


    @override
    def create_configuration_account_manager(self, rolename: str, test_plan_node: TestPlanConstellationNode) -> tuple[NodeConfiguration, AccountManager | None]:
        app = test_plan_node.parameter_or_raise(APP_PAR, { APP_PAR.name:  'Mastodon' }) # Let user give a more descriptive name if they want to
        app_version = test_plan_node.parameter(APP_VERSION_PAR)
        hostname = test_plan_node.parameter_or_raise(HOSTNAME_PAR)
        verify_tls_certificate = test_plan_node.parameter_or_raise(VERIFY_API_TLS_CERTIFICATE_PAR, { VERIFY_API_TLS_CERTIFICATE_PAR.name: 'true' })

        if not hostname:
            hostname = prompt_user_parse_validate(
                    f'Enter the hostname for the Mastodon Node of constellation role "{ rolename }" (node parameter "hostname"): ',
                    parse_validate=hostname_validate)

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

        return (
            NodeWithMastodonApiConfiguration(
                node_driver=self,
                app=cast(str, app),
                app_version=cast(str, app_version),
                hostname=hostname,
                verify_tls_certificate=verify_tls_certificate
            ),
            DefaultAccountManager(accounts, non_existing_accounts)
        )


    @override
    def _provision_node(self, rolename: str, config: NodeConfiguration, account_manager: AccountManager | None) -> FediverseNode:
        return MastodonNode(rolename, config, cast(AccountManager, account_manager))
