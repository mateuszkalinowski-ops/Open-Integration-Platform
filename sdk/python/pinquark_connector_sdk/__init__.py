"""Pinquark Connector SDK — framework for building Open Integration Platform connectors."""

from pinquark_connector_sdk.app import ConnectorApp
from pinquark_connector_sdk.auth import OAuth2Manager
from pinquark_connector_sdk.decorators import action, trigger, webhook
from pinquark_connector_sdk.legacy import augment_legacy_fastapi_app

__all__ = ["ConnectorApp", "OAuth2Manager", "action", "trigger", "webhook", "augment_legacy_fastapi_app"]
