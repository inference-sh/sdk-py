"""Files API - namespaced file operations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Inference, AsyncInference, UploadFileOptions


class FilesAPI:
    """Synchronous Files API.

    Example:
        ```python
        client = inference(api_key="...")

        # Upload a file from path
        file = client.files.upload("/path/to/image.png")

        # Upload from bytes
        file = client.files.upload(image_bytes, UploadFileOptions(
            filename="image.png",
            content_type="image/png"
        ))
        ```
    """

    def __init__(self, client: "Inference") -> None:
        self._client = client

    def upload(
        self,
        data: Union[str, bytes],
        options: Optional["UploadFileOptions"] = None,
    ) -> Dict[str, Any]:
        """Upload a file.

        Args:
            data: File content as bytes, base64 string, data URI, or file path
            options: Upload options (filename, content_type, path, public)

        Returns:
            The uploaded file object with uri, filename, etc.
        """
        return self._client.upload_file(data, options)


class AsyncFilesAPI:
    """Asynchronous Files API.

    Example:
        ```python
        client = async_inference(api_key="...")

        # Upload a file from path
        file = await client.files.upload("/path/to/image.png")
        ```
    """

    def __init__(self, client: "AsyncInference") -> None:
        self._client = client

    async def upload(
        self,
        data: Union[str, bytes],
        options: Optional["UploadFileOptions"] = None,
    ) -> Dict[str, Any]:
        """Upload a file.

        See FilesAPI.upload for full documentation.
        """
        return await self._client.upload_file(data, options)
