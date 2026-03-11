from __future__ import annotations

from core.connector_registry import ConnectorManifest, ConnectorRegistry


def _manifest(**overrides) -> ConnectorManifest:
    base = {
        "name": "demo",
        "category": "ecommerce",
        "version": "1.0.0",
        "display_name": "Demo Commerce",
        "description": "A searchable commerce connector",
        "interface": "ecommerce",
        "country": "PL",
        "capabilities": ["orders.read"],
        "events": ["order.created"],
        "actions": ["order.fetch"],
        "config_schema": {"required": ["client_id", "client_secret"], "optional": ["sandbox_mode"]},
        "credential_validation": {"required_fields": ["client_id", "client_secret"]},
        "oauth2": {"authorization_url": "https://example.test/oauth"},
        "webhooks": {"order.created": {"signature_header": "X-Test"}},
    }
    base.update(overrides)
    return ConnectorManifest(**base)


def test_connector_manifest_derives_catalog_metadata() -> None:
    manifest = _manifest()

    assert manifest.auth_type == "oauth2"
    assert manifest.supports_oauth2 is True
    assert manifest.sandbox_available is True
    assert manifest.has_webhooks is True


def test_registry_search_supports_phase4_filters() -> None:
    registry = ConnectorRegistry()
    registry._connectors = {
        "ecommerce/demo/1.0.0": _manifest(),
        "other/token/1.0.0": _manifest(
            name="token-demo",
            category="other",
            status="beta",
            display_name="Token Demo",
            description="Slack-style token connector",
            country="US",
            config_schema={"required": ["api_token"], "optional": []},
            credential_validation={"required_fields": ["api_token"]},
            oauth2={},
            webhooks={},
            events=["message.created"],
            actions=["message.send"],
        ),
    }

    assert [c.name for c in registry.search(q="searchable")] == ["demo"]
    assert [c.name for c in registry.search(country="US")] == ["token-demo"]
    assert [c.name for c in registry.search(auth_type="token")] == ["token-demo"]
    assert [c.name for c in registry.search(status="beta")] == ["token-demo"]
    assert [c.name for c in registry.search(has_webhooks=True)] == ["demo"]
    assert [c.name for c in registry.search(action="message.send")] == ["token-demo"]
