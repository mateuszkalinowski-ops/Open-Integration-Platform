"""Async FTP and SFTP client abstraction.

Provides a unified interface for both FTP (aioftp) and SFTP (asyncssh)
protocols, with retry logic and structured logging.
"""

import asyncio
import contextlib
import io
import logging
import os
import stat as stat_module
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

import aioftp
import asyncssh

from src.config import FtpAccountConfig
from src.ftp_client.schemas import FileInfo

logger = logging.getLogger(__name__)

DEFAULT_CONNECT_TIMEOUT = 15.0
DEFAULT_OPERATION_TIMEOUT = 60.0


class FtpSftpClient:
    """Unified async client for FTP and SFTP operations."""

    def __init__(
        self,
        account: FtpAccountConfig,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        operation_timeout: float = DEFAULT_OPERATION_TIMEOUT,
    ) -> None:
        self._account = account
        self._connect_timeout = connect_timeout
        self._operation_timeout = operation_timeout

    @property
    def protocol(self) -> str:
        return self._account.protocol

    @property
    def host(self) -> str:
        return self._account.host

    @property
    def port(self) -> int:
        return self._account.effective_port

    def _resolve_path(self, remote_path: str) -> str:
        base = PurePosixPath(self._account.base_path)
        combined = base / PurePosixPath(remote_path)
        resolved = PurePosixPath(os.path.normpath(str(combined)))
        try:
            resolved.relative_to(base)
        except ValueError as err:
            raise ValueError(f"Path escapes base directory: {remote_path}") from err
        return str(resolved)

    # ------------------------------------------------------------------
    # FTP operations
    # ------------------------------------------------------------------

    async def _ftp_list(self, remote_path: str) -> list[FileInfo]:
        resolved = self._resolve_path(remote_path)
        async with self._ftp_connect() as client:
            files: list[FileInfo] = []
            async for path, info in client.list(resolved):
                name = PurePosixPath(path).name
                if name in (".", ".."):
                    continue
                is_dir = info.get("type") == "dir"
                size = int(info.get("size", 0))
                modify_str = info.get("modify")
                modified = None
                if modify_str:
                    with contextlib.suppress(ValueError):
                        modified = datetime.strptime(modify_str, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
                files.append(
                    FileInfo(
                        filename=name,
                        path=str(PurePosixPath(resolved) / name),
                        size=size,
                        is_directory=is_dir,
                        modified_at=modified,
                    )
                )
            return files

    async def _ftp_upload(self, remote_path: str, data: bytes) -> int:
        resolved = self._resolve_path(remote_path)
        async with self._ftp_connect() as client:
            parent = str(PurePosixPath(resolved).parent)
            await self._ftp_ensure_dir(client, parent)
            stream = io.BytesIO(data)
            async with client.upload_stream(resolved) as dest:
                while chunk := stream.read(65536):
                    await dest.write(chunk)
            return len(data)

    async def _ftp_download(self, remote_path: str) -> bytes:
        resolved = self._resolve_path(remote_path)
        async with self._ftp_connect() as client:
            buf = io.BytesIO()
            async with client.download_stream(resolved) as src:
                async for chunk in src.iter_by_block(65536):
                    buf.write(chunk)
            return buf.getvalue()

    async def _ftp_delete(self, remote_path: str) -> None:
        resolved = self._resolve_path(remote_path)
        async with self._ftp_connect() as client:
            await client.remove_file(resolved)

    async def _ftp_move(self, source: str, destination: str) -> None:
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)
        async with self._ftp_connect() as client:
            await client.rename(src, dst)

    async def _ftp_mkdir(self, remote_path: str) -> None:
        resolved = self._resolve_path(remote_path)
        async with self._ftp_connect() as client:
            await self._ftp_ensure_dir(client, resolved)

    async def _ftp_test(self) -> dict[str, Any]:
        async with self._ftp_connect() as client:
            cwd = await client.get_current_directory()
            return {
                "status": "connected",
                "protocol": "ftp",
                "host": self._account.host,
                "port": self._account.effective_port,
                "current_directory": str(cwd),
            }

    async def _ftp_ensure_dir(self, client: aioftp.Client, path: str) -> None:
        with contextlib.suppress(aioftp.StatusCodeError):
            await client.make_directory(path)

    def _ftp_connect(self) -> aioftp.Client:
        return aioftp.Client.context(
            host=self._account.host,
            port=self._account.effective_port,
            user=self._account.username or "anonymous",
            password=self._account.password or "",
            socket_timeout=self._operation_timeout,
            passive_commands={"pasv"} if self._account.passive_mode else set(),
        )

    # ------------------------------------------------------------------
    # SFTP operations
    # ------------------------------------------------------------------

    async def _sftp_connect(self) -> asyncssh.SSHClientConnection:
        known_hosts_env = os.environ.get("SFTP_KNOWN_HOSTS", "")
        if known_hosts_env:
            known_hosts: Any = known_hosts_env
        elif os.path.isfile(os.path.expanduser("~/.ssh/known_hosts")):
            known_hosts = os.path.expanduser("~/.ssh/known_hosts")
        else:
            raise ConnectionError(
                "SFTP connection refused: no known_hosts file found. "
                "Set SFTP_KNOWN_HOSTS env var or populate ~/.ssh/known_hosts."
            )
        kwargs: dict[str, Any] = {
            "host": self._account.host,
            "port": self._account.effective_port,
            "known_hosts": known_hosts,
        }
        if self._account.username:
            kwargs["username"] = self._account.username
        if self._account.password:
            kwargs["password"] = self._account.password
        if self._account.private_key:
            kwargs["client_keys"] = [asyncssh.import_private_key(self._account.private_key)]

        return await asyncio.wait_for(
            asyncssh.connect(**kwargs),
            timeout=self._connect_timeout,
        )

    async def _sftp_list(self, remote_path: str) -> list[FileInfo]:
        resolved = self._resolve_path(remote_path)
        conn = await self._sftp_connect()
        try:
            async with conn.start_sftp_client() as sftp:
                entries = await sftp.readdir(resolved)
                files: list[FileInfo] = []
                for entry in entries:
                    name = entry.filename
                    if name in (".", ".."):
                        continue
                    attrs = entry.attrs
                    is_dir = stat_module.S_ISDIR(attrs.permissions) if attrs.permissions else False
                    modified = None
                    if attrs.mtime is not None:
                        modified = datetime.fromtimestamp(attrs.mtime, tz=UTC)
                    files.append(
                        FileInfo(
                            filename=name,
                            path=str(PurePosixPath(resolved) / name),
                            size=attrs.size or 0,
                            is_directory=is_dir,
                            modified_at=modified,
                            permissions=oct(attrs.permissions)[-3:] if attrs.permissions else None,
                        )
                    )
                return files
        finally:
            conn.close()
            await conn.wait_closed()

    async def _sftp_upload(self, remote_path: str, data: bytes) -> int:
        resolved = self._resolve_path(remote_path)
        conn = await self._sftp_connect()
        try:
            async with conn.start_sftp_client() as sftp:
                parent = str(PurePosixPath(resolved).parent)
                with contextlib.suppress(asyncssh.SFTPError):
                    await sftp.makedirs(parent)
                async with sftp.open(resolved, "wb") as f:
                    await f.write(data)
                return len(data)
        finally:
            conn.close()
            await conn.wait_closed()

    async def _sftp_download(self, remote_path: str) -> bytes:
        resolved = self._resolve_path(remote_path)
        conn = await self._sftp_connect()
        try:
            async with conn.start_sftp_client() as sftp, sftp.open(resolved, "rb") as f:
                return await f.read()
        finally:
            conn.close()
            await conn.wait_closed()

    async def _sftp_delete(self, remote_path: str) -> None:
        resolved = self._resolve_path(remote_path)
        conn = await self._sftp_connect()
        try:
            async with conn.start_sftp_client() as sftp:
                await sftp.remove(resolved)
        finally:
            conn.close()
            await conn.wait_closed()

    async def _sftp_move(self, source: str, destination: str) -> None:
        src = self._resolve_path(source)
        dst = self._resolve_path(destination)
        conn = await self._sftp_connect()
        try:
            async with conn.start_sftp_client() as sftp:
                await sftp.rename(src, dst)
        finally:
            conn.close()
            await conn.wait_closed()

    async def _sftp_mkdir(self, remote_path: str) -> None:
        resolved = self._resolve_path(remote_path)
        conn = await self._sftp_connect()
        try:
            async with conn.start_sftp_client() as sftp:
                with contextlib.suppress(asyncssh.SFTPError):
                    await sftp.makedirs(resolved)
        finally:
            conn.close()
            await conn.wait_closed()

    async def _sftp_test(self) -> dict[str, Any]:
        conn = await self._sftp_connect()
        try:
            async with conn.start_sftp_client() as sftp:
                cwd = await sftp.realpath(".")
                return {
                    "status": "connected",
                    "protocol": "sftp",
                    "host": self._account.host,
                    "port": self._account.effective_port,
                    "current_directory": str(cwd),
                }
        finally:
            conn.close()
            await conn.wait_closed()

    # ------------------------------------------------------------------
    # Unified public API
    # ------------------------------------------------------------------

    async def list_files(self, remote_path: str = "/") -> list[FileInfo]:
        if self.protocol == "sftp":
            return await self._sftp_list(remote_path)
        return await self._ftp_list(remote_path)

    async def upload(self, remote_path: str, data: bytes) -> int:
        if self.protocol == "sftp":
            return await self._sftp_upload(remote_path, data)
        return await self._ftp_upload(remote_path, data)

    async def download(self, remote_path: str) -> bytes:
        if self.protocol == "sftp":
            return await self._sftp_download(remote_path)
        return await self._ftp_download(remote_path)

    async def delete(self, remote_path: str) -> None:
        if self.protocol == "sftp":
            await self._sftp_delete(remote_path)
        else:
            await self._ftp_delete(remote_path)

    async def move(self, source: str, destination: str) -> None:
        if self.protocol == "sftp":
            await self._sftp_move(source, destination)
        else:
            await self._ftp_move(source, destination)

    async def mkdir(self, remote_path: str) -> None:
        if self.protocol == "sftp":
            await self._sftp_mkdir(remote_path)
        else:
            await self._ftp_mkdir(remote_path)

    async def test_connection(self) -> dict[str, Any]:
        if self.protocol == "sftp":
            return await self._sftp_test()
        return await self._ftp_test()
