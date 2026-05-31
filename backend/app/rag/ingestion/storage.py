"""Raw-file storage behind a ``FileStorage`` port.

Cloudinary is used in production; a local-disk fallback keeps the app runnable without
Cloudinary credentials (useful for tests / first run).
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Protocol

from app.core.config import Settings, get_settings


class FileStorage(Protocol):
    async def upload(self, path: str, *, public_id: str | None = None) -> tuple[str | None, str]:
        """Store the file and return ``(public_id, url)``."""
        ...


class CloudinaryStorage:
    def __init__(self, settings: Settings) -> None:
        import cloudinary

        self._folder = settings.cloudinary_folder or None
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    async def upload(self, path: str, *, public_id: str | None = None) -> tuple[str | None, str]:
        import cloudinary.uploader

        def _do() -> dict:
            return cloudinary.uploader.upload(
                path,
                public_id=public_id,
                folder=self._folder,  # e.g. "finsight" → assets land under that folder
                resource_type="auto",
                use_filename=True,
                unique_filename=True,
            )

        result = await asyncio.to_thread(_do)
        return result.get("public_id"), result["secure_url"]


class LocalStorage:
    """Copies files under a local directory; returns a ``file://`` URL."""

    def __init__(self, base_dir: str = "uploads") -> None:
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    async def upload(self, path: str, *, public_id: str | None = None) -> tuple[str | None, str]:
        src = Path(path)
        dest = self.base / (public_id or src.name)
        await asyncio.to_thread(shutil.copy, src, dest)
        return None, dest.resolve().as_uri()


def get_file_storage(settings: Settings | None = None) -> FileStorage:
    settings = settings or get_settings()
    if settings.cloudinary_cloud_name and settings.cloudinary_api_key:
        return CloudinaryStorage(settings)
    return LocalStorage()
