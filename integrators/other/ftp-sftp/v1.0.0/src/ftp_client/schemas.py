"""Pydantic request/response models for FTP/SFTP operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Metadata about a remote file."""

    filename: str
    path: str
    size: int = 0
    is_directory: bool = False
    modified_at: datetime | None = None
    permissions: str | None = None


class FileUploadRequest(BaseModel):
    remote_path: str = Field(..., description="Remote destination path (directory)")
    filename: str = Field(..., description="File name on the remote server")
    content_base64: str = Field(..., description="File content encoded as base64")
    overwrite: bool = Field(default=False, description="Overwrite if file already exists")


class FileUploadResponse(BaseModel):
    status: str = "uploaded"
    remote_path: str
    filename: str
    size: int


class FileDownloadResponse(BaseModel):
    filename: str
    remote_path: str
    content_base64: str
    size: int


class FileDeleteRequest(BaseModel):
    remote_path: str = Field(..., description="Path to the file to delete")


class FileMoveRequest(BaseModel):
    source_path: str = Field(..., description="Source file path")
    destination_path: str = Field(..., description="Destination file path")


class DirectoryCreateRequest(BaseModel):
    remote_path: str = Field(..., description="Path of the directory to create")


class DirectoryCreateResponse(BaseModel):
    status: str = "created"
    remote_path: str


class ConnectionTestResponse(BaseModel):
    status: str
    protocol: str
    host: str
    port: int
    server_banner: str = ""
    current_directory: str = ""
