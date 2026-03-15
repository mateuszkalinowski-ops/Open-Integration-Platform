"""Async S3 client wrapping aiobotocore for S3 and S3-compatible storage."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aiobotocore.session import get_session
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from src.config import S3AccountConfig
from src.s3_client.schemas import BucketInfo, ObjectInfo

logger = logging.getLogger(__name__)

DEFAULT_CONNECT_TIMEOUT = 15.0
DEFAULT_READ_TIMEOUT = 60.0


class S3Client:
    """Async client for Amazon S3 and S3-compatible storage."""

    def __init__(
        self,
        account: S3AccountConfig,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
    ) -> None:
        self._account = account
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._session = get_session()

    @property
    def region(self) -> str:
        return self._account.region

    @property
    def endpoint(self) -> str:
        return self._account.endpoint_url

    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator[Any]:
        boto_config = BotoConfig(
            connect_timeout=self._connect_timeout,
            read_timeout=self._read_timeout,
            retries={"max_attempts": 3, "mode": "adaptive"},
            s3={"addressing_style": "path"} if self._account.use_path_style else {},
        )

        kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self._account.region,
            "aws_access_key_id": self._account.aws_access_key_id,
            "aws_secret_access_key": self._account.aws_secret_access_key,
            "config": boto_config,
        }
        if self._account.endpoint_url:
            kwargs["endpoint_url"] = self._account.endpoint_url

        async with self._session.create_client(**kwargs) as client:
            yield client

    async def list_buckets(self) -> list[BucketInfo]:
        async with self._get_client() as client:
            response = await client.list_buckets()
            return [
                BucketInfo(
                    name=b["Name"],
                    creation_date=b.get("CreationDate"),
                )
                for b in response.get("Buckets", [])
            ]

    async def create_bucket(self, bucket: str, region: str = "") -> None:
        effective_region = region or self._account.region
        async with self._get_client() as client:
            kwargs: dict[str, Any] = {"Bucket": bucket}
            if effective_region and effective_region != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {
                    "LocationConstraint": effective_region,
                }
            await client.create_bucket(**kwargs)

    async def delete_bucket(self, bucket: str) -> None:
        async with self._get_client() as client:
            await client.delete_bucket(Bucket=bucket)

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[ObjectInfo]:
        async with self._get_client() as client:
            kwargs: dict[str, Any] = {
                "Bucket": bucket,
                "MaxKeys": max_keys,
            }
            if prefix:
                kwargs["Prefix"] = prefix

            response = await client.list_objects_v2(**kwargs)
            return [
                ObjectInfo(
                    key=obj["Key"],
                    bucket=bucket,
                    size=obj.get("Size", 0),
                    last_modified=obj.get("LastModified"),
                    etag=obj.get("ETag", "").strip('"'),
                    storage_class=obj.get("StorageClass", ""),
                )
                for obj in response.get("Contents", [])
            ]

    async def upload_object(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload an object and return its ETag."""
        async with self._get_client() as client:
            response = await client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return response.get("ETag", "").strip('"')

    async def download_object(self, bucket: str, key: str) -> tuple[bytes, str]:
        """Download an object and return (data, content_type)."""
        async with self._get_client() as client:
            response = await client.get_object(Bucket=bucket, Key=key)
            async with response["Body"] as stream:
                data = await stream.read()
            content_type = response.get("ContentType", "application/octet-stream")
            return data, content_type

    async def delete_object(self, bucket: str, key: str) -> None:
        async with self._get_client() as client:
            await client.delete_object(Bucket=bucket, Key=key)

    async def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        destination_bucket: str,
        destination_key: str,
    ) -> None:
        async with self._get_client() as client:
            await client.copy_object(
                Bucket=destination_bucket,
                Key=destination_key,
                CopySource={"Bucket": source_bucket, "Key": source_key},
            )

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        client_method = "get_object" if method.upper() == "GET" else "put_object"
        async with self._get_client() as client:
            url = await client.generate_presigned_url(
                client_method,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url

    async def head_object(self, bucket: str, key: str) -> dict[str, Any]:
        async with self._get_client() as client:
            return await client.head_object(Bucket=bucket, Key=key)

    async def test_connection(self) -> dict[str, Any]:
        """Test S3 connectivity by listing buckets."""
        try:
            buckets = await self.list_buckets()
            return {
                "status": "connected",
                "region": self._account.region,
                "endpoint": self._account.endpoint_url,
                "buckets_accessible": len(buckets),
            }
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "Unknown")
            raise ConnectionError(f"S3 connection failed: {error_code} — {exc}") from exc
