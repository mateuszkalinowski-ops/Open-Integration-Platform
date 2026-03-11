"""Pinquark Connector SDK — framework for building Open Integration Platform connectors."""

from pinquark_connector_sdk.app import ConnectorApp
from pinquark_connector_sdk.decorators import action, trigger, webhook

__all__ = ["ConnectorApp", "action", "trigger", "webhook"]
