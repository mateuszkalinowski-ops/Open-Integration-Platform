"""Tests for configuration settings."""

from src.config import S3AccountConfig, Settings


def test_s3_account_config_defaults():
    account = S3AccountConfig(
        name="test",
        aws_access_key_id="AKIA...",
        aws_secret_access_key="secret",
    )
    assert account.region == "us-east-1"
    assert account.endpoint_url == ""
    assert account.use_path_style is False
    assert account.default_bucket == ""
    assert account.environment == "production"


def test_s3_account_config_custom():
    account = S3AccountConfig(
        name="minio",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        region="us-east-1",
        endpoint_url="http://localhost:9000",
        use_path_style=True,
        default_bucket="test-bucket",
        environment="development",
    )
    assert account.endpoint_url == "http://localhost:9000"
    assert account.use_path_style is True
    assert account.default_bucket == "test-bucket"


def test_settings_defaults():
    s = Settings()
    assert s.app_name == "s3-integrator"
    assert s.app_version == "1.0.0"
    assert s.port == 8000
    assert s.polling_enabled is False
    assert s.max_retries == 3
