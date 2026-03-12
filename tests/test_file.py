"""Tests for File class lazy loading and JSON schema generation."""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel, Field

from inferencesh import File


class TestFileLazyLoading:
    """Test that File downloads lazily when .path is accessed."""

    def test_local_path_resolves_immediately(self):
        """Local paths should resolve immediately without lazy loading."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test content")
            path = f.name

        try:
            file = File(uri=path)
            # Should be resolved immediately for local paths
            assert file._resolved is True
            assert file._path == os.path.abspath(path)
            assert file.path == os.path.abspath(path)
        finally:
            os.unlink(path)

    def test_url_does_not_download_on_construction(self):
        """URLs should NOT download when File is constructed."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url') as mock_download:
            file = File(uri=url)

            # Should NOT have called download yet
            mock_download.assert_not_called()

            # Should have URI available
            assert file.uri == url

            # Should NOT be resolved yet
            assert file._resolved is False
            assert file._path is None

    def test_url_downloads_on_path_access(self):
        """URLs should download when .path is accessed."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url') as mock_download:
            # Make mock set _path like real download would
            def fake_download():
                file._path = "/tmp/cached/image.jpg"
            mock_download.side_effect = fake_download

            file = File(uri=url)

            # Access .path - should trigger download
            _ = file.path

            # Should have called download
            mock_download.assert_called_once()
            assert file._resolved is True

    def test_uri_access_does_not_trigger_download(self):
        """Accessing .uri should NOT trigger download."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url') as mock_download:
            file = File(uri=url)

            # Access .uri multiple times
            _ = file.uri
            _ = file.uri
            _ = file.uri

            # Should NOT have called download
            mock_download.assert_not_called()

    def test_is_resolved_without_download(self):
        """is_resolved() should not trigger download."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url') as mock_download:
            file = File(uri=url)

            # Check resolution status
            assert file.is_resolved() is False

            # Should NOT have called download
            mock_download.assert_not_called()

    def test_is_local_without_download(self):
        """is_local() should not trigger download."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url') as mock_download:
            file = File(uri=url)

            # Check local status
            assert file.is_local() is False

            # Should NOT have called download
            mock_download.assert_not_called()

    def test_serialization_does_not_trigger_download(self):
        """Serializing to dict should NOT trigger download."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url') as mock_download:
            file = File(uri=url)

            # Serialize
            data = file.to_dict()

            # Should NOT have called download
            mock_download.assert_not_called()

            # Should have URI but no path
            assert data["uri"] == url
            assert "path" not in data or data.get("path") is None

    def test_data_uri_does_not_decode_on_construction(self):
        """Data URIs should NOT decode when File is constructed."""
        data_uri = "data:text/plain;base64,SGVsbG8gV29ybGQ="

        with patch.object(File, '_decode_data_uri') as mock_decode:
            file = File(uri=data_uri)

            # Should NOT have called decode yet
            mock_decode.assert_not_called()

            # Should have URI available
            assert file.uri == data_uri
            assert file._resolved is False

    def test_data_uri_decodes_on_path_access(self):
        """Data URIs should decode when .path is accessed."""
        data_uri = "data:text/plain;base64,SGVsbG8gV29ybGQ="

        with patch.object(File, '_decode_data_uri') as mock_decode:
            def fake_decode():
                file._path = "/tmp/cached/file.txt"
            mock_decode.side_effect = fake_decode

            file = File(uri=data_uri)

            # Access .path
            _ = file.path

            # Should have called decode
            mock_decode.assert_called_once()


class TestFileJsonSchema:
    """Test that File generates correct JSON schema via Pydantic."""

    def test_file_field_schema(self):
        """File field should generate {"type": "string", "format": "file"}."""
        class TestModel(BaseModel):
            image: File = Field(description="Input image")

        schema = TestModel.model_json_schema()

        # Check the image field
        assert "properties" in schema
        assert "image" in schema["properties"]

        image_schema = schema["properties"]["image"]
        assert image_schema.get("type") == "string"
        assert image_schema.get("format") == "file"
        assert image_schema.get("description") == "Input image"

    def test_optional_file_field_schema(self):
        """Optional File field should also have format: file."""
        from typing import Optional

        class TestModel(BaseModel):
            image: Optional[File] = Field(default=None, description="Optional image")

        schema = TestModel.model_json_schema()

        image_schema = schema["properties"]["image"]
        # Should still have format: file (may be in anyOf for Optional)
        if "anyOf" in image_schema:
            # Find the non-null option
            for option in image_schema["anyOf"]:
                if option.get("type") != "null":
                    assert option.get("format") == "file"
                    break
        else:
            assert image_schema.get("format") == "file"

    def test_file_list_schema(self):
        """List[File] should have items with format: file."""
        from typing import List

        class TestModel(BaseModel):
            images: List[File] = Field(description="Multiple images")

        schema = TestModel.model_json_schema()

        images_schema = schema["properties"]["images"]
        assert images_schema.get("type") == "array"
        assert "items" in images_schema
        assert images_schema["items"].get("type") == "string"
        assert images_schema["items"].get("format") == "file"

    def test_file_pydantic_validation(self):
        """File should validate from string URL."""
        class TestModel(BaseModel):
            image: File

        with patch.object(File, '_download_url'):
            # Validate from URL string
            model = TestModel(image="https://example.com/image.jpg")

            assert model.image.uri == "https://example.com/image.jpg"

    def test_file_pydantic_validation_from_dict(self):
        """File should validate from dict with uri/path."""
        class TestModel(BaseModel):
            image: File

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test")
            path = f.name

        try:
            model = TestModel(image={"path": path})
            assert model.image._path == os.path.abspath(path)
        finally:
            os.unlink(path)

    def test_file_pydantic_serialization(self):
        """File should serialize without triggering download."""
        class TestModel(BaseModel):
            image: File

        with patch.object(File, '_download_url'):
            model = TestModel(image="https://example.com/image.jpg")

            # Serialize to dict
            data = model.model_dump()

            # Should have uri, not path (since not downloaded)
            assert data["image"]["uri"] == "https://example.com/image.jpg"
            assert data["image"].get("path") is None
