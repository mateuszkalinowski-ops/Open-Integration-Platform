"""Tests for Pydantic schema validation."""

import base64
from datetime import UTC, datetime

from src.ftp_client.schemas import (
    ConnectionTestResponse,
    DirectoryCreateRequest,
    FileDeleteRequest,
    FileDownloadResponse,
    FileInfo,
    FileMoveRequest,
    FileUploadRequest,
    FileUploadResponse,
)


def test_file_info_creation():
    info = FileInfo(
        filename="test.txt",
        path="/home/test.txt",
        size=256,
        is_directory=False,
        modified_at=datetime(2026, 1, 1, tzinfo=UTC),
        permissions="755",
    )
    assert info.filename == "test.txt"
    assert info.size == 256
    assert not info.is_directory


def test_file_info_directory():
    info = FileInfo(
        filename="subdir",
        path="/home/subdir",
        is_directory=True,
    )
    assert info.is_directory
    assert info.size == 0


def test_file_upload_request_validation():
    content = base64.b64encode(b"test data").decode()
    req = FileUploadRequest(
        remote_path="/upload",
        filename="data.csv",
        content_base64=content,
        overwrite=True,
    )
    assert req.filename == "data.csv"
    assert req.overwrite is True


def test_file_upload_response():
    resp = FileUploadResponse(remote_path="/upload", filename="data.csv", size=100)
    assert resp.status == "uploaded"


def test_file_download_response():
    content = base64.b64encode(b"content").decode()
    resp = FileDownloadResponse(
        filename="file.txt",
        remote_path="/file.txt",
        content_base64=content,
        size=7,
    )
    assert base64.b64decode(resp.content_base64) == b"content"


def test_file_delete_request():
    req = FileDeleteRequest(remote_path="/old/file.log")
    assert req.remote_path == "/old/file.log"


def test_file_move_request():
    req = FileMoveRequest(source_path="/a/file.txt", destination_path="/b/file.txt")
    assert req.source_path == "/a/file.txt"
    assert req.destination_path == "/b/file.txt"


def test_directory_create_request():
    req = DirectoryCreateRequest(remote_path="/new/dir")
    assert req.remote_path == "/new/dir"


def test_connection_test_response():
    resp = ConnectionTestResponse(
        status="connected",
        protocol="sftp",
        host="sftp.example.com",
        port=22,
        current_directory="/home/user",
    )
    assert resp.status == "connected"
    assert resp.protocol == "sftp"
