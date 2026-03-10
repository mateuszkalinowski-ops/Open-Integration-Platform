"""Tests for Pydantic schema validation."""

import base64
from datetime import datetime, timezone

from src.s3_client.schemas import (
    BucketCreateRequest,
    BucketInfo,
    ConnectionTestResponse,
    ObjectCopyRequest,
    ObjectDeleteRequest,
    ObjectDownloadResponse,
    ObjectInfo,
    ObjectUploadRequest,
    ObjectUploadResponse,
    PresignRequest,
    PresignResponse,
)


def test_object_info_creation():
    info = ObjectInfo(
        key="data/test.txt",
        bucket="my-bucket",
        size=256,
        last_modified=datetime(2026, 1, 1, tzinfo=timezone.utc),
        etag="abc123",
        storage_class="STANDARD",
    )
    assert info.key == "data/test.txt"
    assert info.size == 256
    assert info.bucket == "my-bucket"


def test_object_info_defaults():
    info = ObjectInfo(key="file.txt", bucket="b")
    assert info.size == 0
    assert info.etag == ""
    assert info.last_modified is None


def test_bucket_info():
    info = BucketInfo(
        name="my-bucket",
        creation_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert info.name == "my-bucket"


def test_object_upload_request_validation():
    content = base64.b64encode(b"test data").decode()
    req = ObjectUploadRequest(
        bucket="my-bucket",
        key="data/file.csv",
        content_base64=content,
        content_type="text/csv",
    )
    assert req.key == "data/file.csv"
    assert req.content_type == "text/csv"


def test_object_upload_response():
    resp = ObjectUploadResponse(
        bucket="my-bucket", key="data/file.csv", size=100, etag="abc",
    )
    assert resp.status == "uploaded"


def test_object_download_response():
    content = base64.b64encode(b"content").decode()
    resp = ObjectDownloadResponse(
        key="file.txt",
        bucket="my-bucket",
        content_base64=content,
        size=7,
        content_type="text/plain",
    )
    assert base64.b64decode(resp.content_base64) == b"content"


def test_object_delete_request():
    req = ObjectDeleteRequest(bucket="my-bucket", key="old/file.log")
    assert req.key == "old/file.log"


def test_object_copy_request():
    req = ObjectCopyRequest(
        source_bucket="bucket-a",
        source_key="file.txt",
        destination_bucket="bucket-b",
        destination_key="archive/file.txt",
    )
    assert req.source_bucket == "bucket-a"
    assert req.destination_key == "archive/file.txt"


def test_presign_request_defaults():
    req = PresignRequest(bucket="my-bucket", key="file.txt")
    assert req.expires_in == 3600
    assert req.method == "GET"


def test_presign_request_put_method():
    req = PresignRequest(bucket="my-bucket", key="file.txt", method="PUT")
    assert req.method == "PUT"


def test_presign_request_invalid_method_raises():
    from pydantic import ValidationError

    try:
        PresignRequest(bucket="my-bucket", key="file.txt", method="DELETE")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


def test_presign_response():
    resp = PresignResponse(
        url="https://s3.example.com/...",
        bucket="my-bucket",
        key="file.txt",
        expires_in=3600,
        method="GET",
    )
    assert resp.url.startswith("https://")


def test_bucket_create_request():
    req = BucketCreateRequest(bucket="new-bucket", region="eu-west-1")
    assert req.bucket == "new-bucket"


def test_connection_test_response():
    resp = ConnectionTestResponse(
        status="connected",
        region="eu-central-1",
        endpoint="",
        buckets_accessible=5,
    )
    assert resp.status == "connected"
    assert resp.buckets_accessible == 5
