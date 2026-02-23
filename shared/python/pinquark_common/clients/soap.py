"""Shared SOAP client utilities for courier integrations using zeep."""

import json
import logging
from zeep import Client, Transport
from zeep.exceptions import Fault, TransportError
from zeep.helpers import serialize_object

logger = logging.getLogger(__name__)


class SoapClientError(Exception):
    """Raised when a SOAP call fails."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def create_soap_client(
    wsdl_url: str,
    timeout: int = 30,
    operation_timeout: int = 600,
    **kwargs,
) -> Client:
    """Create a zeep SOAP client with standard timeout settings."""
    transport = Transport(timeout=timeout, operation_timeout=operation_timeout)
    try:
        return Client(wsdl_url, transport=transport, **kwargs)
    except Exception as exc:
        logger.error("Failed to create SOAP client for %s: %s", wsdl_url, exc)
        raise SoapClientError(f"Cannot connect to SOAP service: {wsdl_url}") from exc


def soap_to_dict(data: object) -> dict:
    """Convert a zeep response object to a Python dict."""
    return json.loads(json.dumps(serialize_object(data)))


def call_soap(client: Client, operation: str, **kwargs) -> dict:
    """Call a SOAP operation with standard error handling.

    Returns the deserialized response as a dict.
    Raises SoapClientError on transport or SOAP fault errors.
    """
    try:
        service_method = getattr(client.service, operation)
        response = service_method(**kwargs)
        if response is None:
            return {}
        return soap_to_dict(response)
    except TransportError as exc:
        logger.error("SOAP transport error calling %s: %s", operation, exc)
        raise SoapClientError(
            str(exc.message) if hasattr(exc, 'message') else str(exc),
            status_code=getattr(exc, 'status_code', 502),
        ) from exc
    except Fault as exc:
        logger.error("SOAP fault calling %s: %s", operation, exc.message)
        raise SoapClientError(exc.message, status_code=400) from exc
