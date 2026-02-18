from typing import Optional, Union, Any
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
import mimetypes
import os
import urllib.request
import urllib.parse
import hashlib
from pathlib import Path
from tqdm import tqdm


class File:
    """A file in the inference.sh ecosystem.

    Accepts a URL, local path, or dict with uri/path keys.
    URLs are downloaded and cached locally on construction.
    In JSON schema, File fields appear as ``{"type": "string", "format": "file"}``
    because consumers only ever see URL strings after the engine uploads local files.
    """

    uri: Optional[str]
    path: Optional[str]
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
                path = initializer.path
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
        self.path = path
        self.content_type = content_type
        self.size = size
        self.filename = filename
        self._tmp_path: Optional[str] = None

        # Resolve: download URLs or normalize local paths
        if self.uri:
            if self._is_url(self.uri):
                self._download_url()
            else:
                self.path = os.path.abspath(self.uri)

        if self.path:
            self.path = os.path.abspath(self.path)
            self._populate_metadata()
        else:
            raise ValueError("Either 'uri' or 'path' must be provided and be valid")

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
    def _pydantic_validate(cls, v: Any) -> "File":
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
        if v.path is not None:
            result["path"] = v.path
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
        return self.path is not None and os.path.exists(self.path)

    def refresh_metadata(self) -> None:
        if self.path and os.path.exists(self.path):
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

    def _download_url(self) -> None:
        original_url = self.uri
        cache_path = self._get_cache_path(original_url)

        if cache_path.exists():
            print(f"Using cached file: {cache_path}")
            self.path = str(cache_path)
            return

        print(f"Downloading URL: {original_url} to {cache_path}")
        try:
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
                self.path = str(cache_path)
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
        if self.path and os.path.exists(self.path):
            if not self.content_type:
                self.content_type = self._guess_content_type()
            if not self.size:
                self.size = self._get_file_size()
            if not self.filename:
                self.filename = self._get_filename()

    def _guess_content_type(self) -> Optional[str]:
        return mimetypes.guess_type(self.path)[0]

    def _get_file_size(self) -> int:
        return os.path.getsize(self.path)

    def _get_filename(self) -> str:
        return os.path.basename(self.path)
