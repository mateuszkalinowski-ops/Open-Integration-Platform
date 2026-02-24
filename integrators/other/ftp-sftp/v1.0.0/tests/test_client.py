"""Tests for FtpSftpClient path resolution and protocol dispatch."""

from src.config import FtpAccountConfig
from src.ftp_client.client import FtpSftpClient


def test_resolve_path_absolute():
    account = FtpAccountConfig(name="t", host="h", base_path="/data")
    client = FtpSftpClient(account)
    assert client._resolve_path("/absolute/path") == "/absolute/path"


def test_resolve_path_relative():
    account = FtpAccountConfig(name="t", host="h", base_path="/data")
    client = FtpSftpClient(account)
    assert client._resolve_path("reports/q1.csv") == "/data/reports/q1.csv"


def test_resolve_path_with_root_base():
    account = FtpAccountConfig(name="t", host="h", base_path="/")
    client = FtpSftpClient(account)
    assert client._resolve_path("file.txt") == "/file.txt"


def test_protocol_property_sftp():
    account = FtpAccountConfig(name="t", host="h", protocol="sftp")
    client = FtpSftpClient(account)
    assert client.protocol == "sftp"


def test_protocol_property_ftp():
    account = FtpAccountConfig(name="t", host="h", protocol="ftp")
    client = FtpSftpClient(account)
    assert client.protocol == "ftp"


def test_host_and_port():
    account = FtpAccountConfig(name="t", host="ftp.example.com", protocol="ftp", port=2121)
    client = FtpSftpClient(account)
    assert client.host == "ftp.example.com"
    assert client.port == 2121
