"""
"""

import time
from typing import cast, override

from feditest.nodedrivers.mastodon import (
    AccountOnNodeWithMastodonAPI,
    AuthenticatedMastodonApiClient,
    NodeWithMastodonAPI
)
from feditest.protocols.fediverse import ROLE_ACCOUNT_FIELD, USERID_ACCOUNT_FIELD

from feditest.reporting import trace
from feditest.testplan import TestPlanNodeAccountField, TestPlanNodeParameter
from feditest.utils import boolean_parse_validate, prompt_user_parse_validate


VERIFY_API_TLS_CERTIFICATE_PAR = TestPlanNodeParameter(
    'verify_api_tls_certificate',
    """If set to false, accessing the Mastodon API will be performed without checking TLS certificates.""",
    validate=boolean_parse_validate
)

def _oauth_token_validate(candidate: str) -> str | None:
    """
    Validate a WordPress "Enable Mastodon Apps" app client API token. Avoids user input errors.
    FIXME this is a wild guess and can be better.
    """
    candidate = candidate.strip()
    return candidate if len(candidate)>10 else None


OAUTH_TOKEN_ACCOUNT_FIELD = TestPlanNodeAccountField(
        'oauth_token',
        """OAuth token of a user so the "Enable Mastodon apps" API can be invoked.""",
        _oauth_token_validate
)


class WordPressAccount(AccountOnNodeWithMastodonAPI):
    """
    Compare with MastodonOAuthTokenAccount.
    """
    def __init__(self, role: str | None, userid: str, oauth_token: str | None, internal_userid: int = -1):
        """
        internal_userid: the number needed to identify the account for oauth token provisioning. There may be better ways
                         of doing this
        The oauth_token may be None. In which case we dynamically obtain one.
        """
        super().__init__(role, userid)
        self._oauth_token = oauth_token
        self._internal_userid = internal_userid
        self._mastodon_client: AuthenticatedMastodonApiClient | None = None # Allocated as needed


    @staticmethod
    def create_from_account_info_in_testplan(account_info_in_testplan: dict[str, str | None], context_msg: str = ''):
        """
        Parses the information provided in an "account" dict of TestPlanConstellationNode
        """
        userid = USERID_ACCOUNT_FIELD.get_validate_from_or_raise(account_info_in_testplan, context_msg)
        role = ROLE_ACCOUNT_FIELD.get_validate_from(account_info_in_testplan, context_msg)
        oauth_token = OAUTH_TOKEN_ACCOUNT_FIELD.get_validate_from_or_raise(account_info_in_testplan, context_msg)
        return WordPressAccount(role, userid, oauth_token)


    @property
    def mastodon_client(self) -> AuthenticatedMastodonApiClient:
        if self._mastodon_client is None:
            node = cast(NodeWithMastodonAPI, self._node)
            oauth_app = node._obtain_mastodon_oauth_app()
            oauth_token = self.oauth_token(oauth_app.client_id)
            trace(f'Logging into WordPress at "{ oauth_app.api_base_url }" with userid "{ self.userid }" with OAuth token "{ oauth_token }".')
            self._mastodon_client = AuthenticatedMastodonApiClient(oauth_app, self, oauth_token)
        return self._mastodon_client


    @override
    @property
    def internal_userid(self) -> int:
        if self._internal_userid >= 0:
            return self._internal_userid
        return self.account_dict['id']


    def oauth_token(self, oauth_client_id: str) -> str:
        """
        Helper to dynamically provision an OAuth token if we don't have one yet.
        """
        if not self._oauth_token:
            real_node = cast(WordPressPlusPluginsNode, self._node)
            self._oauth_token = real_node._provision_oauth_token_for(self, oauth_client_id)
        return self._oauth_token


class WordPressPlusPluginsNode(NodeWithMastodonAPI):
    """
    A Node running WordPress with the ActivityPub plugin.
    """
    def _provision_oauth_token_for(self, account: WordPressAccount, oauth_client_id: str) -> str:
        ret = prompt_user_parse_validate(f'Enter the OAuth token for the Mastodon API for user "{ account.userid  }"'
                                       + f' on constellation role "{ self.rolename }", OAuth client id "{ oauth_client_id }" (user field "{ OAUTH_TOKEN_ACCOUNT_FIELD }"): ',
                                       parse_validate=_oauth_token_validate)
        return ret


    @override
    def _run_poor_mans_cron(self) -> None:
        # Seems we need two HTTP GETs
        url = f'https://{ self.hostname }/wp-cron.php?doing_wp_cron'
        session = self._obtain_requests_session()

        # There must be a better way. But this seems to do it. 15 might be enough. 10 might not.
        for _ in range(20):
            time.sleep(1)
            trace('Triggering wp-cron at { url }')
            session.get(url)
