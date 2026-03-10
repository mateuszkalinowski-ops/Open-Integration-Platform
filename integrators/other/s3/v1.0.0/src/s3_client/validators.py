"""Validators for S3 connector input data."""

import re

BUCKET_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.\-]{1,61}[a-z0-9]$")
KEY_MAX_LENGTH = 1024


class S3ValidationError(ValueError):
    pass


def validate_bucket_name(bucket: str) -> str:
    if not bucket:
        raise S3ValidationError("Bucket name cannot be empty")
    if not BUCKET_NAME_PATTERN.match(bucket):
        raise S3ValidationError(
            f"Invalid bucket name '{bucket}'. Must be 3-63 characters, "
            "lowercase letters, numbers, dots, and hyphens only."
        )
    if ".." in bucket:
        raise S3ValidationError("Bucket name cannot contain consecutive dots")
    return bucket


def validate_object_key(key: str) -> str:
    if not key:
        raise S3ValidationError("Object key cannot be empty")
    if len(key) > KEY_MAX_LENGTH:
        raise S3ValidationError(f"Object key exceeds maximum length of {KEY_MAX_LENGTH}")
    return key
