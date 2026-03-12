from typing import Optional, Union, Any, Tuple
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
import base64
import mimetypes
import os
import re
import urllib.request
import urllib.parse
import hashlib
from pathlib import Path
from tqdm import tqdm


class File:
    """A file in the inference.sh ecosystem.

    Accepts a URL, local path, or dict with uri/path keys.
    URLs are downloaded lazily when `path` is first accessed.
    In JSON schema, File fields appear as ``{"type": "string", "format": "file"}``
    because consumers only ever see URL strings after the engine uploads local files.

    For API wrapper apps that only need to forward the URL, use `uri` directly
    without accessing `path` to avoid unnecessary downloads.
    """

    uri: Optional[str]
    content_type: Optional[str]
    size: Optional[int]
    filename: Optional[str]

    def __init__(
        self,
        initializer: Union[str, dict, "File", None] = None,
        *,
        uri: Optional[str] = None,
        path: Optional[str] = None,
        content_type: Optional[str] = None,
        size: Optional[int] = None,
        filename: Optional[str] = None,
    ):
        # Accept positional string/dict/File or keyword args
        if initializer is not None:
            if isinstance(initializer, str):
                uri = initializer
            elif isinstance(initializer, File):
                uri = initializer.uri
                path = initializer._path
                content_type = content_type or initializer.content_type
                size = size or initializer.size
                filename = filename or initializer.filename
            elif isinstance(initializer, dict):
                uri = initializer.get("uri", uri)
                path = initializer.get("path", path)
                content_type = initializer.get("content_type", content_type)
                size = initializer.get("size", size)
                filename = initializer.get("filename", filename)
            else:
                raise ValueError(f"Invalid input for File: {initializer}")

        if not uri and not path:
            raise ValueError("Either 'uri' or 'path' must be provided")

        self.uri = uri
        self._path: Optional[str] = None
        self._resolved = False
        self.content_type = content_type
        self.size = size
        self.filename = filename
        self._tmp_path: Optional[str] = None

        # If a local path was provided directly, use it immediately
        if path:
            self._path = os.path.abspath(path)
            self._resolved = True
            self._populate_metadata()
        # If URI is a local path (not URL or data URI), resolve it immediately
        elif self.uri and not self._is_url(self.uri) and not self._is_data_uri(self.uri):
            self._path = os.path.abspath(self.uri)
            self._resolved = True
            self._populate_metadata()
        # Otherwise, defer resolution until path is accessed

    @property
    def path(self) -> Optional[str]:
        """Local file path. Downloads the file lazily if needed."""
        if self._resolved:
            return self._path

        # Lazy resolution for URLs and data URIs
        if self.uri:
            if self._is_data_uri(self.uri):
                self._decode_data_uri()
            elif self._is_url(self.uri):
                self._download_url()

        self._resolved = True
        return self._path

    @path.setter
    def path(self, value: Optional[str]) -> None:
        """Set the local path directly."""
        self._path = value
        self._resolved = True

    # --- Pydantic integration (custom type, not a BaseModel) ---

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._pydantic_validate,
            serialization=core_schema.plain_serializer_function_ser_schema(cls._pydantic_serialize),
            metadata={
                "pydantic_js_functions": [
                    lambda _s, _h: {"type": "string", "format": "file"}
                ]
            },
        )

    @classmethod
    def _pydantic_validate(cls, v: Any) -> Optional["File"]:
        # Empty values become None
        if v is None or v == "" or v == {}:
            return None
        if isinstance(v, cls):
            return v
        if isinstance(v, str):
            return cls(v)
        if isinstance(v, dict):
            return cls(**v)
        raise ValueError(f"Invalid input for File: {v}")

    @staticmethod
    def _pydantic_serialize(v: "File") -> dict:
        result: dict[str, Any] = {}
        if v.uri is not None:
            result["uri"] = v.uri
        # Use _path to avoid triggering download during serialization
        if v._path is not None:
            result["path"] = v._path
        if v.content_type is not None:
            result["content_type"] = v.content_type
        if v.size is not None:
            result["size"] = v.size
        if v.filename is not None:
            result["filename"] = v.filename
        return result

    # --- Cache ---

    @classmethod
    def get_cache_dir(cls) -> Path:
        if cache_dir := os.environ.get("FILE_CACHE_DIR"):
            path = Path(cache_dir)
        else:
            path = Path.home() / ".cache" / "inferencesh" / "files"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_cache_path(self, url: str) -> Path:
        parsed_url = urllib.parse.urlparse(url)
        url_components = parsed_url.netloc + parsed_url.path
        if parsed_url.query:
            url_components += "?" + parsed_url.query
        url_hash = hashlib.sha256(url_components.encode()).hexdigest()[:12]

        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = "download"

        cache_dir = self.get_cache_dir() / url_hash
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / filename

    # --- Helpers ---

    @classmethod
    def from_path(cls, path: Union[str, os.PathLike]) -> "File":
        return cls(uri=str(path))

    def exists(self) -> bool:
        """Check if the file exists locally (triggers download if needed)."""
        return self.path is not None and os.path.exists(self.path)

    def is_resolved(self) -> bool:
        """Check if the file has been downloaded/resolved without triggering download."""
        return self._resolved

    def is_local(self) -> bool:
        """Check if we have a local path without triggering download."""
        return self._path is not None and os.path.exists(self._path)

    def refresh_metadata(self) -> None:
        """Re-read metadata from disk (triggers download if needed)."""
        if self.path and os.path.exists(self._path):
            self.content_type = self._guess_content_type()
            self.size = self._get_file_size()
            self.filename = self._get_filename()

    def to_dict(self) -> dict:
        return self._pydantic_serialize(self)

    # --- Internal ---

    @staticmethod
    def _is_url(path: str) -> bool:
        parsed = urllib.parse.urlparse(path)
        return parsed.scheme in ("http", "https")

    @staticmethod
    def _is_data_uri(path: str) -> bool:
        return path.startswith("data:")

    @staticmethod
    def _parse_data_uri(uri: str) -> Tuple[str, str, bytes]:
        """Parse a data URI and return (media_type, extension, decoded_data).

        Supports formats:
        - data:image/jpeg;base64,/9j/4AAQ...
        - data:text/plain,Hello%20World
        - data:;base64,SGVsbG8=  (defaults to text/plain)
        """
        # Match: data:[<mediatype>][;base64],<data>
        match = re.match(r"^data:([^;,]*)?(?:;(base64))?,(.*)$", uri, re.DOTALL)
        if not match:
            raise ValueError(f"Invalid data URI format")

        media_type = match.group(1) or "text/plain"
        is_base64 = match.group(2) == "base64"
        data_str = match.group(3)

        if is_base64:
            # Handle URL-safe base64 and padding
            data_str = data_str.replace("-", "+").replace("_", "/")
            # Add padding if needed
            padding = 4 - (len(data_str) % 4)
            if padding != 4:
                data_str += "=" * padding
            try:
                data = base64.b64decode(data_str)
            except Exception as e:
                raise ValueError(f"Failed to decode base64 data: {e}")
        else:
            # URL-encoded data
            data = urllib.parse.unquote(data_str).encode("utf-8")

        # Get file extension from media type
        ext = mimetypes.guess_extension(media_type) or ""
        # mimetypes returns .jpe for image/jpeg, prefer .jpg
        if ext == ".jpe":
            ext = ".jpg"

        return media_type, ext, data

    def _decode_data_uri(self) -> None:
        """Decode a data URI and save to cache."""
        uri = self.uri

        # Create cache path based on hash of the data URI
        uri_hash = hashlib.sha256(uri.encode()).hexdigest()[:16]
        cache_dir = self.get_cache_dir() / "data_uri" / uri_hash

        # Check for existing cached file
        if cache_dir.exists():
            cached_files = list(cache_dir.iterdir())
            if cached_files:
                self._path = str(cached_files[0])
                self._populate_metadata()
                return

        # Parse and decode
        media_type, ext, data = self._parse_data_uri(uri)

        # Set content_type from the data URI if not already set
        if not self.content_type:
            self.content_type = media_type

        # Create cache directory and write file
        cache_dir.mkdir(parents=True, exist_ok=True)
        filename = f"file{ext}" if ext else "file"
        cache_path = cache_dir / filename

        try:
            with open(cache_path, "wb") as f:
                f.write(data)
            self._path = str(cache_path)
            self._populate_metadata()
        except IOError as e:
            raise RuntimeError(f"Failed to write decoded data URI to {cache_path}: {e}")

    def _download_url(self) -> None:
        original_url = self.uri
        cache_path = self._get_cache_path(original_url)

        if cache_path.exists():
            print(f"Using cached file: {cache_path}")
            self._path = str(cache_path)
            self._populate_metadata()
            return

        print(f"Downloading URL: {original_url} to {cache_path}")
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = str(cache_path) + ".tmp"
            self._tmp_path = tmp_path

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            req = urllib.request.Request(original_url, headers=headers)

            try:
                with urllib.request.urlopen(req) as response:
                    total_size = 0
                    try:
                        if hasattr(response, "headers") and response.headers is not None:
                            cl = response.headers.get("content-length")
                            total_size = int(cl) if cl is not None else 0
                        elif hasattr(response, "getheader"):
                            cl = response.getheader("content-length")
                            total_size = int(cl) if cl is not None else 0
                    except Exception:
                        total_size = 0

                    block_size = 1024

                    with tqdm(total=total_size, unit="iB", unit_scale=True) as pbar:
                        with open(self._tmp_path, "wb") as out_file:
                            while True:
                                non_chunking = False
                                try:
                                    buffer = response.read(block_size)
                                except TypeError:
                                    buffer = response.read()
                                    non_chunking = True
                                if not buffer:
                                    break
                                out_file.write(buffer)
                                try:
                                    pbar.update(len(buffer))
                                except Exception:
                                    pass
                                if non_chunking:
                                    break

                os.rename(self._tmp_path, cache_path)
                self._tmp_path = None
                self._path = str(cache_path)
                self._populate_metadata()
            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                raise RuntimeError(f"Failed to download URL {original_url}: {str(e)}")
            except IOError as e:
                raise RuntimeError(f"Failed to write downloaded file to {self._tmp_path}: {str(e)}")
        except Exception as e:
            if self._tmp_path:
                try:
                    os.unlink(self._tmp_path)
                except (OSError, IOError):
                    pass
            raise RuntimeError(f"Error downloading URL {original_url}: {str(e)}")

    def __del__(self):
        if hasattr(self, "_tmp_path") and self._tmp_path:
            try:
                os.unlink(self._tmp_path)
            except (OSError, IOError):
                pass

    def _populate_metadata(self) -> None:
        if self._path and os.path.exists(self._path):
            if not self.content_type:
                self.content_type = self._guess_content_type()
            if not self.size:
                self.size = self._get_file_size()
            if not self.filename:
                self.filename = self._get_filename()

    def _guess_content_type(self) -> Optional[str]:
        return mimetypes.guess_type(self._path)[0] if self._path else None

    def _get_file_size(self) -> int:
        return os.path.getsize(self._path) if self._path else 0

    def _get_filename(self) -> str:
        return os.path.basename(self._path) if self._path else ""
