"""Orchestration facade for FTP/SFTP operations across multiple accounts."""

import base64
import fnmatch
import logging
from typing import Any

from src.config import settings
from src.ftp_client.client import FtpSftpClient
from src.ftp_client.schemas import (
    ConnectionTestResponse,
    DirectoryCreateResponse,
    FileDeleteRequest,
    FileDownloadResponse,
    FileInfo,
    FileMoveRequest,
    FileUploadRequest,
    FileUploadResponse,
)
from src.services.account_manager import AccountManager

logger = logging.getLogger(__name__)


class FtpSftpIntegration:
    """High-level integration facade managing per-account FTP/SFTP clients."""

    def __init__(self, account_manager: AccountManager) -> None:
        self._account_manager = account_manager
        self._clients: dict[str, FtpSftpClient] = {}

    def _get_client(self, account_name: str) -> FtpSftpClient:
        if account_name not in self._clients:
            account = self._account_manager.get_account(account_name)
            if not account:
                raise ValueError(f"Account '{account_name}' not found")
            self._clients[account_name] = FtpSftpClient(
                account=account,
                connect_timeout=settings.connect_timeout,
                operation_timeout=settings.operation_timeout,
            )
        return self._clients[account_name]

    def remove_client(self, account_name: str) -> None:
        self._clients.pop(account_name, None)

    async def test_connection(self, account_name: str) -> ConnectionTestResponse:
        client = self._get_client(account_name)
        result = await client.test_connection()
        return ConnectionTestResponse(**result)

    async def list_files(
        self,
        account_name: str,
        remote_path: str = "/",
        pattern: str | None = None,
    ) -> list[FileInfo]:
        client = self._get_client(account_name)
        files = await client.list_files(remote_path)
        if pattern:
            files = [f for f in files if fnmatch.fnmatch(f.filename, pattern)]
        logger.info(
            "Listed %d files at %s (account=%s, pattern=%s)",
            len(files),
            remote_path,
            account_name,
            pattern,
        )
        return files

    async def upload_file(
        self,
        account_name: str,
        request: FileUploadRequest,
    ) -> FileUploadResponse:
        client = self._get_client(account_name)
        data = base64.b64decode(request.content_base64)
        remote_full = f"{request.remote_path.rstrip('/')}/{request.filename}"

        if not request.overwrite:
            existing = await client.list_files(request.remote_path)
            for f in existing:
                if f.filename == request.filename:
                    raise FileExistsError(
                        f"File '{request.filename}' already exists at '{request.remote_path}'. "
                        f"Set overwrite=true to replace."
                    )

        size = await client.upload(remote_full, data)
        logger.info(
            "Uploaded %s (%d bytes) to %s (account=%s)",
            request.filename,
            size,
            remote_full,
            account_name,
        )
        return FileUploadResponse(
            remote_path=request.remote_path,
            filename=request.filename,
            size=size,
        )

    async def download_file(
        self,
        account_name: str,
        remote_path: str,
    ) -> FileDownloadResponse:
        client = self._get_client(account_name)
        data = await client.download(remote_path)
        from pathlib import PurePosixPath

        filename = PurePosixPath(remote_path).name
        logger.info(
            "Downloaded %s (%d bytes) from %s (account=%s)",
            filename,
            len(data),
            remote_path,
            account_name,
        )
        return FileDownloadResponse(
            filename=filename,
            remote_path=remote_path,
            content_base64=base64.b64encode(data).decode("ascii"),
            size=len(data),
        )

    async def delete_file(
        self,
        account_name: str,
        request: FileDeleteRequest,
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        await client.delete(request.remote_path)
        logger.info("Deleted %s (account=%s)", request.remote_path, account_name)
        return {"status": "deleted", "remote_path": request.remote_path}

    async def move_file(
        self,
        account_name: str,
        request: FileMoveRequest,
    ) -> dict[str, Any]:
        client = self._get_client(account_name)
        await client.move(request.source_path, request.destination_path)
        logger.info(
            "Moved %s -> %s (account=%s)",
            request.source_path,
            request.destination_path,
            account_name,
        )
        return {
            "status": "moved",
            "source_path": request.source_path,
            "destination_path": request.destination_path,
        }

    async def create_directory(
        self,
        account_name: str,
        remote_path: str,
    ) -> DirectoryCreateResponse:
        client = self._get_client(account_name)
        await client.mkdir(remote_path)
        logger.info("Created directory %s (account=%s)", remote_path, account_name)
        return DirectoryCreateResponse(remote_path=remote_path)
