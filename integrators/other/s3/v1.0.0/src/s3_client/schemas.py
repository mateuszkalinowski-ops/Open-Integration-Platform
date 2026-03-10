"""Pydantic request/response models for S3 operations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ObjectInfo(BaseModel):
    """Metadata about an S3 object."""

    key: str
    bucket: str
    size: int = 0
    last_modified: datetime | None = None
    etag: str = ""
    storage_class: str = ""
    content_type: str = ""


class BucketInfo(BaseModel):
    """Metadata about an S3 bucket."""

    name: str
    creation_date: datetime | None = None


class ObjectUploadRequest(BaseModel):
    bucket: str = Field(..., description="Target bucket name")
    key: str = Field(..., description="Object key (path in bucket)")
    content_base64: str = Field(..., description="File content encoded as base64")
    content_type: str = Field(default="application/octet-stream", description="MIME content type")


class ObjectUploadResponse(BaseModel):
    status: str = "uploaded"
    bucket: str
    key: str
    size: int
    etag: str = ""


class ObjectDownloadResponse(BaseModel):
    key: str
    bucket: str
    content_base64: str
    size: int
    content_type: str = ""


class ObjectDeleteRequest(BaseModel):
    bucket: str = Field(..., description="Bucket name")
    key: str = Field(..., description="Object key to delete")


class ObjectCopyRequest(BaseModel):
    source_bucket: str = Field(..., description="Source bucket name")
    source_key: str = Field(..., description="Source object key")
    destination_bucket: str = Field(..., description="Destination bucket name")
    destination_key: str = Field(..., description="Destination object key")


class ObjectCopyResponse(BaseModel):
    status: str = "copied"
    source_bucket: str
    source_key: str
    destination_bucket: str
    destination_key: str


class PresignRequest(BaseModel):
    bucket: str = Field(..., description="Bucket name")
    key: str = Field(..., description="Object key")
    expires_in: int = Field(default=3600, description="URL expiration in seconds")
    method: Literal["GET", "PUT"] = Field(default="GET", description="HTTP method (GET or PUT)")


class PresignResponse(BaseModel):
    url: str
    bucket: str
    key: str
    expires_in: int
    method: str


class BucketCreateRequest(BaseModel):
    bucket: str = Field(..., description="Bucket name to create")
    region: str = Field(default="", description="AWS region for the bucket")


class BucketCreateResponse(BaseModel):
    status: str = "created"
    bucket: str
    region: str = ""


class ConnectionTestResponse(BaseModel):
    status: str
    region: str
    endpoint: str = ""
    buckets_accessible: int = 0
