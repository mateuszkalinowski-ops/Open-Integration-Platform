"""Tier 3 functional checks — Account-based connectors (email, ftp-sftp).

Generic fallback for connectors in the "other" category that use
account-based listing endpoints.
"""

from typing import Any

import httpx

from src.checks.common import get_check
from src.discovery import VerificationTarget


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url
    account = (target.credentials or {}).get("account_name", "verification-agent")

    results.append(await get_check(client, f"{base}/accounts", "list_accounts"))

    if target.manifest.name == "email-client":
        results.append(
            await get_check(
                client,
                f"{base}/folders",
                "list_folders",
                params={"account_name": account},
            )
        )
    elif target.manifest.name == "ftp-sftp":
        results.append(
            await get_check(
                client,
                f"{base}/files",
                "list_files",
                params={"account_name": account, "remote_path": "/"},
            )
        )

    return results
