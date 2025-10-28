"""
"""

from typing import Any, cast

from feditest.nodedrivers import APP_PAR, APP_VERSION_PAR, HOSTNAME_PAR
from feditest.nodedrivers.mastodon import NodeWithMastodonApiConfiguration
from feditest.nodedrivers.ubosgears import (
    UbosNodeConfiguration,
    UbosNodeDeployConfiguration,
    UbosNodeDriver,
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


class MastodonUbosNodeConfiguration(UbosNodeDeployConfiguration, NodeWithMastodonApiConfiguration):
    def __init__(self,
        node_driver: 'UbosNodeDriver',
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
    ):
        super(UbosNodeDeployConfiguration,self).__init__(
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


    # Python 3.12 @override
    @staticmethod
    def create_from_node_in_testplan(
        test_plan_node: TestPlanConstellationNode,
        node_driver: 'UbosNodeDriver',
        appconfigjson: dict[str, Any],
        defaults: dict[str, str | None] | None = None
    ) -> 'UbosNodeConfiguration':
        """
        This is largely copied from the superclass.
        """
        real_node_driver = cast(UbosNodeDriver, node_driver) # Make linter happy
        siteid = test_plan_node.parameter(SITEID_PAR, defaults=defaults) or UbosNodeConfiguration._generate_siteid()
        appconfigid = test_plan_node.parameter(APPCONFIGID_PAR, defaults=defaults) or UbosNodeConfiguration._generate_appconfigid()
        app = test_plan_node.parameter_or_raise(APP_PAR, defaults=defaults)
        hostname = test_plan_node.parameter(HOSTNAME_PAR) or registry_singleton().obtain_new_hostname(app)
        admin_userid = test_plan_node.parameter(ADMIN_USERID_PAR, defaults=defaults) or 'feditestadmin'
        admin_username = test_plan_node.parameter(ADMIN_USERNAME_PAR, defaults=defaults) or 'feditestadmin'
        admin_credential = test_plan_node.parameter(ADMIN_CREDENTIAL_PAR, defaults=defaults) or UbosNodeConfiguration._generate_credential()
        admin_email = test_plan_node.parameter(ADMIN_EMAIL_PAR, defaults=defaults) or f'{ admin_userid }@{ hostname }'
        start_delay_1 = test_plan_node.parameter(START_DELAY_PAR, defaults=defaults)
        if start_delay_1:
            if isinstance(float, start_delay_1):
                start_delay = cast(float, start_delay_1)
            else:
                start_delay = float(start_delay_1)
        else:
            start_delay = 10.0 # 10 sec should be good enough

        if test_plan_node.parameter(BACKUPFILE_PAR):
            raise TestPlanNodeParameterMalformedError(BACKUP_APPCONFIGID_PAR, ' must not be given for MastodonUbosNodeDriver')
        if test_plan_node.parameter(BACKUP_APPCONFIGID_PAR):
            raise TestPlanNodeParameterMalformedError(BACKUP_APPCONFIGID_PAR, ' must not be given for MastodonUbosNodeDriver')

        return MastodonUbosNodeConfiguration(
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
            app_version = test_plan_node.parameter(APP_VERSION_PAR, defaults=defaults),
            tlskey = test_plan_node.parameter(TLSKEY_PAR, defaults=defaults),
            tlscert = test_plan_node.parameter(TLSCERT_PAR, defaults=defaults),
            start_delay = start_delay,
            rshcmd = test_plan_node.parameter(RSH_CMD_PAR, defaults=defaults)
        )


    @property
    def verify_tls_certificate(self) -> bool:
        return True

