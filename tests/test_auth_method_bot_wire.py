"""OAuth bot installs and per-scope authorize params (api-v1581 / b70ad27 typegen).

``AuthMethod.bot`` carries the provider bot user (Slack) and ``scope_params`` maps
each scope to extra authorize query parameters (Discord bot permissions).
"""

from typing import Dict, List, Optional, get_type_hints

from inferencesh.types import AuthMethod, AuthMethodBot, AuthMethodKind


def test_auth_method_bot_exposes_scope_and_host_fields():
    hints = get_type_hints(AuthMethodBot)
    assert set(hints) >= {
        "scope_param",
        "scopes",
        "token",
        "granted_scopes",
        "hosts",
    }
    assert hints["scopes"] == List[str]
    assert hints["hosts"] == List[str]


def test_auth_method_bot_models_slack_bot_install():
    bot: AuthMethodBot = {
        "scope_param": "scope",
        "scopes": ["bot:chat:write"],
        "token": "{{token.bot.access_token}}",
        "granted_scopes": "bot:chat:write bot:users:read",
        "hosts": ["slack.com", "api.slack.com"],
    }
    assert bot["scopes"][0].startswith("bot:")
    assert bot["hosts"] == ["slack.com", "api.slack.com"]


def test_auth_method_declares_bot_and_scope_params():
    hints = get_type_hints(AuthMethod)
    assert "bot" in hints
    assert hints["bot"] == Optional[AuthMethodBot]
    assert hints["scope_params"] == Dict[str, Dict[str, str]]


def test_auth_method_oauth_payload_carries_bot_and_scope_params():
    method: AuthMethod = {
        "kind": AuthMethodKind.AUTH_METHOD_O_AUTH2,
        "authorization_endpoint": "https://slack.com/oauth/authorize",
        "scope_params": {
            "bot:chat:write": {"user_scope": "chat:write"},
        },
        "bot": {
            "scope_param": "scope",
            "scopes": ["bot:chat:write"],
            "hosts": ["api.slack.com"],
        },
    }
    assert method["bot"]["scope_param"] == "scope"
    assert method["scope_params"]["bot:chat:write"]["user_scope"] == "chat:write"