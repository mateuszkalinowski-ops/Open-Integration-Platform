"""Orchestration facade for S3 operations across multiple accounts."""

import base64
import logging
from datetime import UTC, datetime
from typing import Any

from src.config import settings
from src.s3_client.client import S3Client
from src.s3_client.schemas import (
    BucketCreateResponse,
    BucketInfo,
    ConnectionTestResponse,
    ObjectCopyRequest,
    ObjectCopyResponse,
    ObjectDeleteRequest,
    ObjectDownloadResponse,
    ObjectInfo,
    ObjectUploadRequest,
    ObjectUploadResponse,
    PresignRequest,
    PresignResponse,
)
from src.s3_client.validators import validate_bucket_name, validate_object_key
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class S3Integration:
    """High-level integration facade managing per-account S3 clients."""

    def __init__(
        self,
        account_manager: AccountManager,
        kafka_producer: Any = None,
    ) -> None:
        self._account_manager = account_manager
        self._kafka_producer = kafka_producer
        self._clients: dict[str, S3Client] = {}

    def _get_client(self, account_name: str) -> S3Client:
        if account_name not in self._clients:
            account = self._account_manager.get_account(account_name)
            if not account:
                raise ValueError(f"Account '{account_name}' not found")
            self._clients[account_name] = S3Client(
                account=account,
                connect_timeout=settings.connect_timeout,
                read_timeout=settings.operation_timeout,
            )
        return self._clients[account_name]

    def remove_client(self, account_name: str) -> None:
        self._clients.pop(account_name, None)

    async def _emit_event(
        self,
        event: str,
        topic: str,
        data: dict[str, Any],
        account_name: str,
    ) -> None:
        if self._kafka_producer:
            from pinquark_common.kafka import wrap_event

            envelope = wrap_event(
                connector_name="s3",
                event=event,
                data=data,
                account_name=account_name,
            )
            await self._kafka_producer.send(topic, envelope, key=account_name)
            logger.debug("Published %s event to Kafka", event)

        if settings.platform_event_notify and settings.platform_api_url:
            try:
                import httpx

                _headers: dict[str, str] = {}
                if settings.platform_internal_secret:
                    _headers["X-Internal-Secret"] = settings.platform_internal_secret
                elif settings.platform_api_key:
                    _headers["X-API-Key"] = settings.platform_api_key
                async with httpx.AsyncClient(timeout=10.0) as http_client:
                    await http_client.post(
                        f"{settings.platform_api_url}/internal/events",
                        json={"connector_name": "s3", "event": event, "data": data},
                        headers=_headers,
                    )
            except (httpx.HTTPError, OSError, ValueError) as exc:
                logger.debug("Failed to notify platform about %s event: %s", event, exc)

    def _resolve_bucket(self, account_name: str, bucket: str) -> str:
        if bucket:
            return bucket
        account = self._account_manager.get_account(account_name)
        if account and account.default_bucket:
            return account.default_bucket
        raise ValueError("No bucket specified and no default_bucket configured for this account")

    async def test_connection(self, account_name: str) -> ConnectionTestResponse:
        client = self._get_client(account_name)
        result = await client.test_connection()
        return ConnectionTestResponse(**result)

    async def list_buckets(self, account_name: str) -> list[BucketInfo]:
        client = self._get_client(account_name)
        buckets = await client.list_buckets()
        logger.info("Listed %d buckets (account=%s)", len(buckets), account_name)
        return buckets

    async def create_bucket(
        self,
        account_name: str,
        bucket: str,
        region: str = "",
    ) -> BucketCreateResponse:
        validate_bucket_name(bucket)
        client = self._get_client(account_name)
        await client.create_bucket(bucket, region)
        effective_region = region or client.region
        logger.info("Created bucket %s in %s (account=%s)", bucket, effective_region, account_name)
        return BucketCreateResponse(bucket=bucket, region=effective_region)

    async def delete_bucket(self, account_name: str, bucket: str) -> dict[str, Any]:
        validate_bucket_name(bucket)
        client = self._get_client(account_name)
        await client.delete_bucket(bucket)
        logger.info("Deleted bucket %s (account=%s)", bucket, account_name)
        return {"status": "deleted", "bucket": bucket}

    async def list_objects(
        self,
        account_name: str,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[ObjectInfo]:
        bucket = self._resolve_bucket(account_name, bucket)
        validate_bucket_name(bucket)
        client = self._get_client(account_name)
        objects = await client.list_objects(bucket, prefix=prefix, max_keys=max_keys)
        logger.info(
            "Listed %d objects in s3://%s/%s (account=%s)",
            len(objects),
            bucket,
            prefix,
            account_name,
        )
        return objects

    async def upload_object(
        self,
        account_name: str,
        request: ObjectUploadRequest,
    ) -> ObjectUploadResponse:
        bucket = self._resolve_bucket(account_name, request.bucket)
        validate_bucket_name(bucket)
        validate_object_key(request.key)

        client = self._get_client(account_name)
        data = base64.b64decode(request.content_base64)
        etag = await client.upload_object(
            bucket,
            request.key,
            data,
            content_type=request.content_type,
        )
        logger.info(
            "Uploaded s3://%s/%s (%d bytes, account=%s)",
            bucket,
            request.key,
            len(data),
            account_name,
        )

        await self._emit_event(
            "object.uploaded",
            settings.kafka_topic_object_uploaded,
            {
                "key": request.key,
                "bucket": bucket,
                "size": len(data),
                "content_type": request.content_type,
                "etag": etag,
                "account_name": account_name,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            account_name,
        )

        return ObjectUploadResponse(
            bucket=bucket,
            key=request.key,
            size=len(data),
            etag=etag,
        )

    async def download_object(
        self,
        account_name: str,
        bucket: str,
        key: str,
    ) -> ObjectDownloadResponse:
        bucket = self._resolve_bucket(account_name, bucket)
        validate_bucket_name(bucket)
        validate_object_key(key)

        client = self._get_client(account_name)
        data, content_type = await client.download_object(bucket, key)
        logger.info(
            "Downloaded s3://%s/%s (%d bytes, account=%s)",
            bucket,
            key,
            len(data),
            account_name,
        )
        return ObjectDownloadResponse(
            key=key,
            bucket=bucket,
            content_base64=base64.b64encode(data).decode("ascii"),
            size=len(data),
            content_type=content_type,
        )

    async def delete_object(
        self,
        account_name: str,
        request: ObjectDeleteRequest,
    ) -> dict[str, Any]:
        bucket = self._resolve_bucket(account_name, request.bucket)
        validate_bucket_name(bucket)
        validate_object_key(request.key)

        client = self._get_client(account_name)
        await client.delete_object(bucket, request.key)
        logger.info("Deleted s3://%s/%s (account=%s)", bucket, request.key, account_name)

        await self._emit_event(
            "object.deleted",
            settings.kafka_topic_object_deleted,
            {
                "key": request.key,
                "bucket": bucket,
                "account_name": account_name,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            account_name,
        )

        return {"status": "deleted", "bucket": bucket, "key": request.key}

    async def copy_object(
        self,
        account_name: str,
        request: ObjectCopyRequest,
    ) -> ObjectCopyResponse:
        validate_bucket_name(request.source_bucket)
        validate_bucket_name(request.destination_bucket)
        validate_object_key(request.source_key)
        validate_object_key(request.destination_key)

        client = self._get_client(account_name)
        await client.copy_object(
            request.source_bucket,
            request.source_key,
            request.destination_bucket,
            request.destination_key,
        )
        logger.info(
            "Copied s3://%s/%s -> s3://%s/%s (account=%s)",
            request.source_bucket,
            request.source_key,
            request.destination_bucket,
            request.destination_key,
            account_name,
        )
        return ObjectCopyResponse(
            source_bucket=request.source_bucket,
            source_key=request.source_key,
            destination_bucket=request.destination_bucket,
            destination_key=request.destination_key,
        )

    async def generate_presigned_url(
        self,
        account_name: str,
        request: PresignRequest,
    ) -> PresignResponse:
        bucket = self._resolve_bucket(account_name, request.bucket)
        validate_bucket_name(bucket)
        validate_object_key(request.key)

        client = self._get_client(account_name)
        url = await client.generate_presigned_url(
            bucket,
            request.key,
            expires_in=request.expires_in,
            method=request.method,
        )
        logger.info(
            "Generated presigned %s URL for s3://%s/%s (account=%s, expires=%ds)",
            request.method,
            bucket,
            request.key,
            account_name,
            request.expires_in,
        )
        return PresignResponse(
            url=url,
            bucket=bucket,
            key=request.key,
            expires_in=request.expires_in,
            method=request.method,
        )
