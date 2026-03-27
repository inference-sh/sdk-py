"""Tests for File class lazy loading and JSON schema generation."""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel, Field

from inferencesh import File


class TestFileEagerLoading:
    """Test that File downloads eagerly on construction (not lazily)."""

    def test_local_path_resolves_immediately(self):
        """Local paths should resolve immediately."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test content")
            path = f.name

        try:
            file = File(uri=path)
            assert file._resolved is True
            assert file._path == os.path.abspath(path)
            assert file.path == os.path.abspath(path)
        finally:
            os.unlink(path)

    def test_url_downloads_on_construction(self):
        """URLs should download eagerly when File is constructed."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url') as mock_download:
            file = File(uri=url)

            # Should have called download during construction
            mock_download.assert_called_once()
            assert file.uri == url
            assert file._resolved is True

    def test_uri_available_after_construction(self):
        """URI should be available after construction."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url'):
            file = File(uri=url)
            assert file.uri == url

    def test_is_resolved_after_construction(self):
        """File should be resolved after construction."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url'):
            file = File(uri=url)
            assert file.is_resolved() is True

    def test_serialization_has_uri(self):
        """Serializing to dict should include URI."""
        url = "https://example.com/image.jpg"

        with patch.object(File, '_download_url'):
            file = File(uri=url)
            data = file.to_dict()
            assert data["uri"] == url

    def test_data_uri_decodes_on_construction(self):
        """Data URIs should decode eagerly on construction."""
        data_uri = "data:text/plain;base64,SGVsbG8gV29ybGQ="

        with patch.object(File, '_decode_data_uri') as mock_decode:
            file = File(uri=data_uri)

            # Should have called decode during construction
            mock_decode.assert_called_once()
            assert file.uri == data_uri


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
