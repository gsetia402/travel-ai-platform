"""Storage provider abstraction — local filesystem and AWS S3."""
import os
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class StorageProvider(ABC):
    """Abstract interface for file storage."""

    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes, return the storage key."""

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Retrieve file bytes by storage key."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove file by storage key."""

    @abstractmethod
    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a time-limited download URL."""

    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier string."""


# --------------- Local Filesystem ---------------

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")


class LocalStorageProvider(StorageProvider):

    def __init__(self, base_dir: str = UPLOAD_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _full_path(self, key: str) -> str:
        return os.path.join(self.base_dir, key)

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._full_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        logger.info(f"[local] stored {key} ({len(data)} bytes)")
        return key

    def download(self, key: str) -> bytes:
        path = self._full_path(key)
        with open(path, "rb") as f:
            return f.read()

    def delete(self, key: str) -> bool:
        path = self._full_path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        # For local dev, return a relative API download path
        return f"/trip-documents/{key}/download"

    def provider_name(self) -> str:
        return "local"


# --------------- AWS S3 ---------------

class S3StorageProvider(StorageProvider):

    def __init__(self):
        import boto3
        self.bucket = os.getenv("S3_BUCKET_NAME", "")
        self.region = os.getenv("AWS_REGION", "ap-south-1")
        self.client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=self.region,
        )
        logger.info(f"[s3] initialized bucket={self.bucket} region={self.region}")

    def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.info(f"[s3] uploaded {key} ({len(data)} bytes)")
        return key

    def download(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> bool:
        self.client.delete_object(Bucket=self.bucket, Key=key)
        return True

    def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def provider_name(self) -> str:
        return "s3"


# --------------- Factory ---------------

_provider: Optional[StorageProvider] = None


def get_storage_provider() -> StorageProvider:
    global _provider
    if _provider is not None:
        return _provider

    provider_type = os.getenv("STORAGE_PROVIDER", "local").lower()
    if provider_type == "s3" and os.getenv("AWS_ACCESS_KEY_ID"):
        try:
            _provider = S3StorageProvider()
        except Exception as e:
            logger.warning(f"S3 init failed, falling back to local: {e}")
            _provider = LocalStorageProvider()
    else:
        _provider = LocalStorageProvider()

    logger.info(f"Storage provider: {_provider.provider_name()}")
    return _provider


def _content_type_from_filename(name: str) -> str:
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    mapping = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return mapping.get(ext, "application/octet-stream")
