"""
"""

from typing import Any, cast

from feditest.nodedrivers import APP_VERSION_PAR, HOSTNAME_PAR
from feditest.nodedrivers.mastodon import NodeWithMastodonApiConfiguration
from feditest.nodedrivers.ubos_admin import (
    UbosAdminNodeConfiguration,
    UbosAdminNodeDeployConfiguration,
    UbosAdminNodeDriver,
    ADMIN_CREDENTIAL_PAR,
    ADMIN_EMAIL_PAR,
    ADMIN_USERID_PAR,
    ADMIN_USERNAME_PAR,
    APPCONFIGID_PAR,
    BACKUP_APPCONFIGID_PAR,
    BACKUPFILE_PAR,
    RSH_CMD_PAR,
    SITEID_PAR,
    START_DELAY_PAR,
    TLSCERT_PAR,
    TLSKEY_PAR
)
from feditest.registry import registry_singleton
from feditest.testplan import TestPlanConstellationNode, TestPlanNodeParameterMalformedError


class MastodonUbosAdminNodeConfiguration(UbosAdminNodeDeployConfiguration, NodeWithMastodonApiConfiguration):
    def __init__(self,
        node_driver: UbosAdminNodeDriver,
        siteid: str,
        appconfigid: str,
        appconfigjson: dict[str,Any],
        admin_userid: str,
        admin_username: str,
        admin_credential: str,
        admin_email: str,
        app: str,
        hostname: str, # Note: switched positions with app_version as it is required here
        app_version: str | None = None,
        tlskey: str | None = None,
        tlscert: str | None = None,
        start_delay: float = 0.0,
        rshcmd: str | None = None,
    ) -> None:
        super(UbosAdminNodeDeployConfiguration,self).__init__(
            node_driver = node_driver,
            siteid = siteid,
            appconfigid = appconfigid,
            appconfigjson = appconfigjson,
            admin_userid = admin_userid,
            admin_username = admin_username,
            admin_credential = admin_credential,
            admin_email = admin_email,
            app = app,
            hostname = hostname,
            app_version = app_version,
            tlskey = tlskey,
            tlscert = tlscert,
            start_delay = start_delay,
            rshcmd = rshcmd,
        )
        # We do the initialization ourselves for the Mastodon part, so we avoid the common ancestor
        self._verify_tls_certificate = True


    @staticmethod
    def create_from_node_in_testplan_with_app(
        test_plan_node: TestPlanConstellationNode,
        node_driver: UbosAdminNodeDriver,
        appconfigjson: dict[str, Any],
        app: str
    ) -> UbosAdminNodeConfiguration:
        """
        This is largely copied from the superclass.
        """
        real_node_driver = cast(UbosAdminNodeDriver, node_driver) # Make linter happy
        siteid = test_plan_node.parameter_or_raise(SITEID_PAR, lambda: UbosAdminNodeConfiguration._generate_siteid())
        appconfigid = test_plan_node.parameter_or_raise(APPCONFIGID_PAR, lambda: UbosAdminNodeConfiguration._generate_appconfigid())
        hostname = test_plan_node.parameter_or_raise(HOSTNAME_PAR, lambda: registry_singleton().obtain_new_hostname(app))
        admin_userid = test_plan_node.parameter_or_raise(ADMIN_USERID_PAR, 'feditestadmin')
        admin_username = test_plan_node.parameter_or_raise(ADMIN_USERNAME_PAR, 'feditestadmin')
        admin_credential = test_plan_node.parameter_or_raise(ADMIN_CREDENTIAL_PAR, lambda: UbosAdminNodeConfiguration._generate_credential())
        admin_email = test_plan_node.parameter_or_raise(ADMIN_EMAIL_PAR, f'{ admin_userid }@{ hostname }')
        start_delay = test_plan_node.parameter_or_raise(START_DELAY_PAR, 10.0) # 10 sec should be good enough

        if test_plan_node.parameter(BACKUPFILE_PAR):
            raise TestPlanNodeParameterMalformedError(BACKUP_APPCONFIGID_PAR, ' must not be given for MastodonUbosAdminNodeDriver')
        if test_plan_node.parameter(BACKUP_APPCONFIGID_PAR):
            raise TestPlanNodeParameterMalformedError(BACKUP_APPCONFIGID_PAR, ' must not be given for MastodonUbosAdminNodeDriver')

        return MastodonUbosAdminNodeConfiguration(
            node_driver = real_node_driver,
            siteid = siteid,
            appconfigid = appconfigid,
            appconfigjson = appconfigjson,
            admin_userid = admin_userid,
            admin_username = admin_username,
            admin_credential = admin_credential,
            admin_email = admin_email,
            app = app,
            hostname = hostname,
            app_version = test_plan_node.parameter(APP_VERSION_PAR),
            tlskey = test_plan_node.parameter(TLSKEY_PAR),
            tlscert = test_plan_node.parameter(TLSCERT_PAR),
            start_delay = start_delay,
            rshcmd = test_plan_node.parameter(RSH_CMD_PAR)
        )


    @property
    def verify_tls_certificate(self) -> bool:
        return True

