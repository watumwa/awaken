"""Storage backends used by the Awakening Saints deployment.

Vercel Functions expose the deployed application bundle as a read-only
filesystem.  Existing media committed to the repository can still be served
as collected static assets, but new uploads must be persisted outside the
function filesystem.

``VercelBlobStorage`` therefore behaves as a hybrid storage backend:

* legacy relative names (for example ``books/example.pdf``) continue to use
  the repository ``MEDIA_ROOT`` for reads and ``/media/`` for public URLs;
* new files are uploaded to a public Vercel Blob store and the returned Blob
  URL is stored in the Django FileField.

The hybrid behaviour lets an existing database continue working without a
one-time media migration while making all future Admin uploads durable.
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile, File
from django.core.files.storage import FileSystemStorage, Storage


class VercelBlobStorage(Storage):
    """Django storage backend for public Vercel Blob media.

    New uploads are stored in Vercel Blob. Existing relative media paths are
    still resolved against the deployed repository's MEDIA_ROOT so that old
    book records do not need to be rewritten immediately.
    """

    access = "public"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = os.getenv("BLOB_READ_WRITE_TOKEN", "").strip()
        self._legacy_storage = FileSystemStorage(
            location=settings.MEDIA_ROOT,
            base_url=settings.MEDIA_URL,
        )

    @staticmethod
    def _is_remote(name: str) -> bool:
        return str(name).startswith(("https://", "http://"))

    def _require_token(self) -> None:
        if not self.token:
            raise ImproperlyConfigured(
                "BLOB_READ_WRITE_TOKEN is required for media uploads on Vercel. "
                "Create/connect a Vercel Blob store to this project and redeploy."
            )

    def _blob_client(self):
        self._require_token()
        try:
            from vercel.blob import BlobClient
        except ImportError as exc:  # pragma: no cover - deployment guard
            raise ImproperlyConfigured(
                "The official 'vercel' Python package is required for Vercel Blob "
                "media storage. Install the dependencies from requirements.txt."
            ) from exc
        return BlobClient(token=self.token)

    def _open(self, name: str, mode: str = "rb") -> File:
        if "b" not in mode:
            raise ValueError("VercelBlobStorage only supports binary file reads.")

        if not self._is_remote(name):
            return self._legacy_storage.open(name, mode)

        response = requests.get(name, timeout=60)
        if response.status_code == 404:
            raise FileNotFoundError(name)
        response.raise_for_status()
        filename = Path(urlparse(name).path).name or "download"
        return ContentFile(response.content, name=filename)

    def _save(self, name: str, content: File) -> str:
        """Upload new media and store the immutable public Blob URL."""
        self._require_token()

        if hasattr(content, "seek"):
            content.seek(0)
        payload = content.read()
        content_type = getattr(content, "content_type", None)
        if not content_type:
            content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"

        client = self._blob_client()
        try:
            uploaded = client.put(
                name,
                payload,
                access=self.access,
                content_type=content_type,
                add_random_suffix=True,
            )
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

        # FileField stores the value returned by Storage.save(). Keeping the
        # complete URL means templates can render .url without another API call.
        return uploaded.url

    def delete(self, name: str) -> None:
        if not name:
            return

        if not self._is_remote(name):
            # Repository media is immutable on Vercel. It may disappear from a
            # database field when replaced, but attempting to unlink it from
            # /var/task would raise Errno 30. Leave the committed asset alone.
            return

        client = self._blob_client()
        try:
            client.delete(name)
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    def exists(self, name: str) -> bool:
        if not name:
            return False
        if not self._is_remote(name):
            return self._legacy_storage.exists(name)
        try:
            response = requests.head(name, timeout=15, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def size(self, name: str) -> int:
        if not self._is_remote(name):
            return self._legacy_storage.size(name)

        response = requests.head(name, timeout=15, allow_redirects=True)
        response.raise_for_status()
        try:
            return int(response.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            return 0

    def url(self, name: str) -> str:
        if self._is_remote(name):
            return name
        return self._legacy_storage.url(name)

    def path(self, name: str) -> str:
        if self._is_remote(name):
            raise NotImplementedError(
                "Vercel Blob files do not have a local filesystem path. Use open()."
            )
        return self._legacy_storage.path(name)

    def get_accessed_time(self, name):
        if not self._is_remote(name):
            return self._legacy_storage.get_accessed_time(name)
        raise NotImplementedError

    def get_created_time(self, name):
        if not self._is_remote(name):
            return self._legacy_storage.get_created_time(name)
        raise NotImplementedError

    def get_modified_time(self, name):
        if not self._is_remote(name):
            return self._legacy_storage.get_modified_time(name)
        raise NotImplementedError
