"""Tests for S3 input validators."""

import pytest

from src.s3_client.validators import S3ValidationError, validate_bucket_name, validate_object_key


class TestBucketNameValidation:
    def test_valid_bucket_name(self):
        assert validate_bucket_name("my-bucket") == "my-bucket"

    def test_valid_bucket_name_with_dots(self):
        assert validate_bucket_name("my.bucket.name") == "my.bucket.name"

    def test_valid_bucket_name_numbers(self):
        assert validate_bucket_name("bucket123") == "bucket123"

    def test_empty_bucket_name_raises(self):
        with pytest.raises(S3ValidationError, match="cannot be empty"):
            validate_bucket_name("")

    def test_too_short_bucket_name_raises(self):
        with pytest.raises(S3ValidationError, match="Invalid bucket name"):
            validate_bucket_name("ab")

    def test_uppercase_bucket_name_raises(self):
        with pytest.raises(S3ValidationError, match="Invalid bucket name"):
            validate_bucket_name("MyBucket")

    def test_consecutive_dots_raises(self):
        with pytest.raises(S3ValidationError, match="consecutive dots"):
            validate_bucket_name("my..bucket")

    def test_bucket_name_with_underscore_raises(self):
        with pytest.raises(S3ValidationError, match="Invalid bucket name"):
            validate_bucket_name("my_bucket")


class TestObjectKeyValidation:
    def test_valid_key(self):
        assert validate_object_key("data/file.csv") == "data/file.csv"

    def test_empty_key_raises(self):
        with pytest.raises(S3ValidationError, match="cannot be empty"):
            validate_object_key("")

    def test_key_too_long_raises(self):
        with pytest.raises(S3ValidationError, match="exceeds maximum length"):
            validate_object_key("x" * 1025)

    def test_long_but_valid_key(self):
        key = "a/" * 500 + "file.txt"
        if len(key) <= 1024:
            assert validate_object_key(key) == key
