"""Generic credential validation driven by connector.yaml configuration.

Replaces per-connector _validate_* functions and hardcoded validator
registries.  Each connector declares its validation requirements in
``credential_validation`` inside connector.yaml; this module interprets
that configuration and executes the appropriate checks.
"""

import asyncio
import base64
import time
from functools import partial
from typing import Any

import httpx

from core.connector_registry import ConnectorManifest, ConnectorRegistry

_TIMEOUT = httpx.Timeout(connect=10, read=15, write=10, pool=10)


def _missing_fields(
    creds: dict[str, str], fields: list[str], service_name: str
) -> dict[str, Any] | None:
    missing = [f for f in fields if not creds.get(f)]
    if missing:
        return {
            "status": "failed",
            "message": f"Missing required {service_name} credentials: {', '.join(missing)}",
        }
    return None


async def _http_credential_check(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    data: dict[str, str] | None = None,
    json_body: dict | None = None,
    auth: tuple[str, str] | None = None,
    params: dict[str, str] | None = None,
    service_name: str = "API",
    success_msg: str = "",
    success_status: int | None = None,
) -> dict[str, Any]:
    """Execute an HTTP request to validate credentials.

    When *success_status* is set (from manifest ``credential_validation.test_request.success_status``),
    only that specific status code is treated as success.
    Otherwise: 401/403 → credential failure; 4xx/5xx → failure; 2xx → success.
    """
    if not success_msg:
        success_msg = f"{service_name} authentication successful"
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.request(
                method, url, headers=headers, data=data, json=json_body,
                auth=auth, params=params,
            )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if success_status is not None:
            if resp.status_code == success_status:
                return {"status": "success", "message": success_msg, "response_time_ms": elapsed_ms}
            return {
                "status": "failed",
                "message": f"{service_name} responded with HTTP {resp.status_code} (expected {success_status})",
                "response_time_ms": elapsed_ms,
            }

        if resp.status_code in (401, 403):
            return {"status": "failed", "message": f"Invalid {service_name} credentials", "response_time_ms": elapsed_ms}
        if resp.status_code >= 400:
            return {"status": "failed", "message": f"{service_name} API error: HTTP {resp.status_code}", "response_time_ms": elapsed_ms}
        return {"status": "success", "message": success_msg, "response_time_ms": elapsed_ms}
    except httpx.ConnectError:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": f"Cannot connect to {service_name} API", "response_time_ms": elapsed_ms}
    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": f"{service_name} API connection timed out", "response_time_ms": elapsed_ms}
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "message": str(exc), "response_time_ms": elapsed_ms}


def _resolve_template(template: str, creds: dict[str, str], defaults: dict[str, str] | None = None) -> str:
    """Replace {field} placeholders with values from credentials or defaults."""
    merged = dict(defaults or {})
    merged.update({k: v for k, v in creds.items() if v})
    result = template
    for key, value in merged.items():
        result = result.replace("{" + key + "}", value)
    return result


def _resolve_dict_template(template: dict, creds: dict[str, str], defaults: dict[str, str] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in template.items():
        if isinstance(v, str):
            out[k] = _resolve_template(v, creds, defaults)
        elif isinstance(v, list):
            out[k] = v
        elif isinstance(v, dict):
            out[k] = _resolve_dict_template(v, creds, defaults)
        else:
            out[k] = v
    return out


def _resolve_sandbox_url(test_cfg: dict, creds: dict[str, str], defaults: dict[str, str]) -> dict[str, str]:
    """Apply sandbox URL override when the sandbox flag is set."""
    sandbox_cfg = test_cfg.get("sandbox")
    if not sandbox_cfg:
        return defaults

    flag = sandbox_cfg.get("flag", "sandbox_mode")
    is_sandbox = creds.get(flag, "false").lower() in ("true", "1", "yes")

    updated = dict(defaults)
    if is_sandbox:
        if "base_url" in sandbox_cfg:
            updated["base_url"] = sandbox_cfg["base_url"]
    else:
        if "production_url" in sandbox_cfg:
            updated["base_url"] = sandbox_cfg["production_url"]
    return updated


async def _validate_email_imap_smtp(creds: dict[str, str], display_name: str) -> dict[str, Any]:
    """Special-case validation for email connectors: test IMAP + SMTP."""
    import imaplib
    import smtplib

    imap_host = creds.get("imap_host", "")
    smtp_host = creds.get("smtp_host", "")
    email_address = creds.get("email_address", "")
    username = creds.get("username", "")
    login = username or email_address
    password = creds.get("password", "")
    imap_port = int(creds.get("imap_port", "993"))
    smtp_port = int(creds.get("smtp_port", "587"))
    use_ssl = creds.get("use_ssl", "true").lower() in ("true", "1", "yes")

    loop = asyncio.get_event_loop()
    results: dict[str, Any] = {}
    start = time.monotonic()

    try:
        def _test_imap() -> str:
            if use_ssl:
                conn = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=10)
            else:
                conn = imaplib.IMAP4(imap_host, imap_port, timeout=10)
            conn.login(login, password)
            conn.logout()
            return "ok"
        await loop.run_in_executor(None, _test_imap)
        results["imap"] = "ok"
    except imaplib.IMAP4.error as exc:
        results["imap"] = f"auth_failed: {exc}"
    except OSError as exc:
        results["imap"] = f"connection_failed: {exc}"
    except Exception as exc:
        results["imap"] = f"error: {exc}"

    try:
        def _test_smtp() -> str:
            if use_ssl and smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.ehlo()
                if use_ssl:
                    server.starttls()
                    server.ehlo()
            server.login(login, password)
            server.quit()
            return "ok"
        await loop.run_in_executor(None, _test_smtp)
        results["smtp"] = "ok"
    except Exception as exc:
        results["smtp"] = f"error: {exc}"

    elapsed_ms = int((time.monotonic() - start) * 1000)

    if results.get("imap") == "ok" and results.get("smtp") == "ok":
        return {
            "status": "success",
            "message": "IMAP and SMTP connection successful",
            "response_time_ms": elapsed_ms,
            "details": results,
        }
    return {
        "status": "failed",
        "message": "Connection test failed",
        "response_time_ms": elapsed_ms,
        "details": results,
    }


async def _execute_test_request(
    test_cfg: dict, creds: dict[str, str], display_name: str
) -> dict[str, Any]:
    """Build and execute an HTTP test request from credential_validation.test_request config."""
    defaults = dict(test_cfg.get("defaults", {}))
    defaults = _resolve_sandbox_url(test_cfg, creds, defaults)

    url = _resolve_template(test_cfg["url_template"], creds, defaults)
    method = test_cfg.get("method", "GET")

    headers: dict[str, str] | None = None
    if "headers_template" in test_cfg:
        headers = _resolve_dict_template(test_cfg["headers_template"], creds, defaults)

    params: dict[str, str] | None = None
    if "params_template" in test_cfg:
        params = _resolve_dict_template(test_cfg["params_template"], creds, defaults)

    json_body: dict | None = None
    if "json_body_template" in test_cfg:
        json_body = _resolve_dict_template(test_cfg["json_body_template"], creds, defaults)

    form_data: dict[str, str] | None = None
    if "form_data_template" in test_cfg:
        form_data = _resolve_dict_template(test_cfg["form_data_template"], creds, defaults)

    auth: tuple[str, str] | None = None
    auth_type = test_cfg.get("auth")
    auth_fields = test_cfg.get("auth_fields", [])
    if auth_type == "basic" and len(auth_fields) >= 2:
        merged = dict(defaults)
        merged.update(creds)
        auth = (merged.get(auth_fields[0], ""), merged.get(auth_fields[1], ""))

    expected_status = test_cfg.get("success_status")

    return await _http_credential_check(
        method, url,
        headers=headers,
        data=form_data,
        json_body=json_body,
        auth=auth,
        params=params,
        service_name=display_name,
        success_msg=f"{display_name} credentials valid",
        success_status=expected_status,
    )


async def _call_connector_validation(
    manifest: ConnectorManifest,
    creds: dict[str, str],
    endpoint_template: str,
) -> dict[str, Any]:
    """Validate by calling the connector's own validation endpoint."""
    account_name = creds.get("account_name", "default")
    endpoint = endpoint_template.replace("{account_name}", account_name)
    base_url = manifest.base_url
    return await _http_credential_check(
        "GET", f"{base_url}{endpoint}",
        service_name=manifest.display_name,
        success_msg=f"{manifest.display_name} connection verified",
    )


async def validate_credentials(
    connector_name: str,
    creds: dict[str, str],
    registry: ConnectorRegistry,
    connector_version: str | None = None,
) -> dict[str, Any]:
    """Generic credential validation driven entirely by connector.yaml.

    When *connector_version* is provided, validates against that specific
    manifest version; otherwise uses the latest discovered version.
    Falls back to config_schema.required if no credential_validation defined.
    """
    manifest = registry.get_by_name_version(connector_name, connector_version)
    if not manifest:
        return {"status": "unsupported", "message": f"Unknown connector: {connector_name}"}
    validation = manifest.credential_validation
    display_name = manifest.display_name

    if not validation:
        required = manifest.config_schema.get("required", [])
        if required:
            fail = _missing_fields(creds, required, display_name)
            if fail:
                return fail
            return {"status": "success", "message": f"{display_name} credentials present"}
        return {"status": "success", "message": f"{display_name} credentials accepted (no validation configured)"}

    required = validation.get("required_fields", [])
    if required:
        fail = _missing_fields(creds, required, display_name)
        if fail:
            return fail

    validate_mode = validation.get("validate_mode")
    if validate_mode == "email_imap_smtp":
        return await _validate_email_imap_smtp(creds, display_name)

    test_cfg = validation.get("test_request")
    if test_cfg:
        return await _execute_test_request(test_cfg, creds, display_name)

    endpoint = validation.get("validate_endpoint")
    if endpoint:
        return await _call_connector_validation(manifest, creds, endpoint)

    return {"status": "success", "message": f"{display_name} credentials present"}
