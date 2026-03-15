"""Tier 3 functional checks — Amazon S3 connector."""

import base64
from typing import Any

import httpx

from src.checks.common import get_check, req_check, result
from src.discovery import VerificationTarget


async def run(
    client: httpx.AsyncClient,
    target: VerificationTarget,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    base = target.base_url
    account = (target.credentials or {}).get("account_name", "verification-agent")

    results.append(await get_check(client, f"{base}/accounts", "list_accounts"))

    results.append(
        await get_check(
            client,
            f"{base}/buckets",
            "list_buckets",
            params={"account_name": account},
        )
    )

    test_bucket = (target.credentials or {}).get("default_bucket", "")

    if test_bucket:
        results.append(
            await get_check(
                client,
                f"{base}/objects",
                "list_objects",
                params={"account_name": account, "bucket": test_bucket, "prefix": "", "max_keys": "10"},
            )
        )
    else:
        results.append(
            result(
                "list_objects",
                "SKIP",
                0,
                error="No default_bucket configured — cannot list objects without explicit bucket",
            )
        )

    test_key = f"verification-agent/test-{account}.txt"
    test_content = base64.b64encode(b"verification-agent-test-file").decode()

    if test_bucket:
        chk, resp = await req_check(
            client,
            "POST",
            f"{base}/objects/upload",
            "upload_object",
            params={"account_name": account},
            json_body={
                "bucket": test_bucket,
                "key": test_key,
                "content_base64": test_content,
                "content_type": "text/plain",
            },
        )
        results.append(chk)

        if resp and resp.status_code in (200, 201):
            results.append(
                await get_check(
                    client,
                    f"{base}/objects/download",
                    "download_object",
                    params={"account_name": account, "bucket": test_bucket, "key": test_key},
                )
            )

            chk_presign, _ = await req_check(
                client,
                "POST",
                f"{base}/objects/presign",
                "presign_object",
                params={"account_name": account},
                json_body={
                    "bucket": test_bucket,
                    "key": test_key,
                    "expires_in": 60,
                    "method": "GET",
                },
            )
            results.append(chk_presign)

            copy_key = f"verification-agent/test-{account}-copy.txt"
            chk_copy, _ = await req_check(
                client,
                "POST",
                f"{base}/objects/copy",
                "copy_object",
                params={"account_name": account},
                json_body={
                    "source_bucket": test_bucket,
                    "source_key": test_key,
                    "destination_bucket": test_bucket,
                    "destination_key": copy_key,
                },
            )
            results.append(chk_copy)

            chk_del_copy, _ = await req_check(
                client,
                "DELETE",
                f"{base}/objects",
                "delete_object_copy_cleanup",
                params={"account_name": account},
                json_body={"bucket": test_bucket, "key": copy_key},
            )
            results.append(chk_del_copy)

            chk_del, _ = await req_check(
                client,
                "DELETE",
                f"{base}/objects",
                "delete_object_cleanup",
                params={"account_name": account},
                json_body={"bucket": test_bucket, "key": test_key},
            )
            results.append(chk_del)
    else:
        results.append(
            result(
                "upload_object",
                "SKIP",
                0,
                error="No default_bucket configured — skipping write tests",
            )
        )

    chk_conn, _ = await req_check(
        client,
        "POST",
        f"{base}/auth/{account}/test",
        "connection_test",
        accept_statuses=(200, 404, 502),
    )
    results.append(chk_conn)

    return results
