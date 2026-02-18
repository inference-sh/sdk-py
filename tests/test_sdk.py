import os
import pytest
import tempfile
from inferencesh import BaseApp, BaseAppInput, BaseAppOutput, File
import urllib.parse

def test_file_creation():
    # Create a temporary file
    with open("test.txt", "w") as f:
        f.write("test")
    
    file = File(path="test.txt")
    assert file.exists()
    assert file.size > 0
    assert file.content_type is not None
    assert file.filename == "test.txt"
    
    os.remove("test.txt")

def test_base_app():
    class TestInput(BaseAppInput):
        text: str

    class TestOutput(BaseAppOutput):
        result: str

    # Use BaseApp directly, don't subclass with implementation
    app = BaseApp()
    import asyncio
    with pytest.raises(NotImplementedError):
        asyncio.run(app.run(TestInput(text="test")))

def test_file_from_local_path():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"test content")
        path = f.name
    
    try:
        # Test creating File from path
        file = File(uri=path)
        assert file.exists()
        assert file.size == len("test content")
        assert file.content_type == "text/plain"
        assert file.filename == os.path.basename(path)
        assert file.path == os.path.abspath(path)
        assert file._tmp_path is None  # Should not create temp file for local paths
    finally:
        os.unlink(path)

def test_file_from_relative_path():
    # Create a file in current directory
    with open("test_relative.txt", "w") as f:
        f.write("relative test")
    
    try:
        file = File(uri="test_relative.txt")
        assert file.exists()
        assert os.path.isabs(file.path)
        assert file.filename == "test_relative.txt"
    finally:
        os.unlink("test_relative.txt")

def test_file_validation():
    # Test empty initialization
    with pytest.raises(ValueError, match="Either 'uri' or 'path' must be provided"):
        File()
    
    # Test invalid input type
    with pytest.raises(ValueError, match="Invalid input for File"):
        File(123)
    
    # Test string input (should work)
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"test content")
        path = f.name
        
    try:
        file = File(path)
        assert isinstance(file, File)
        assert file.uri == path
        assert file.exists()
    finally:
        os.unlink(path)

def test_file_from_url(monkeypatch):
    # Mock URL download
    def mock_urlopen(request):
        class MockResponse:
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass
            
            def read(self):
                return b"mocked content"
        
        return MockResponse()
    
    monkeypatch.setattr(urllib.request, 'urlopen', mock_urlopen)
    
    # Use a unique URL to avoid caching issues
    import time
    url = f"https://example.com/test_{int(time.time() * 1000)}.pdf"
    file = File(uri=url)
    
    try:
        assert file._is_url(url)
        assert file.exists()
        # Check that path is set (either from cache or fresh download)
        assert file.path is not None
        assert file.path.endswith('.pdf')  # Just check the extension
        assert file.content_type == "application/pdf"
    finally:
        # Cleanup - remove the file if it exists
        if file.path and os.path.exists(file.path):
            os.unlink(file.path)

def test_file_metadata_refresh():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        initial_content = b'{"test": "data"}'
        f.write(initial_content)
        path = f.name
    
    try:
        file = File(uri=path)
        initial_size = file.size
        
        # Modify file with significantly more data
        with open(path, 'ab') as f:  # Open in append binary mode
            additional_data = b'\n{"more": "data"}\n' * 10  # Add multiple lines of data
            f.write(additional_data)
        
        # Refresh metadata
        file.refresh_metadata()
        assert file.size > initial_size, f"New size {file.size} should be larger than initial size {initial_size}"
    finally:
        os.unlink(path)

def test_file_cleanup(monkeypatch):
    # Mock URL download - same mock as test_file_from_url
    def mock_urlopen(request):
        class MockResponse:
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass
            
            def read(self):
                return b"mocked content"
        
        return MockResponse()
    
    monkeypatch.setattr(urllib.request, 'urlopen', mock_urlopen)
    
    url = "https://example.com/test.txt"
    file = File(uri=url)
    
    if file._tmp_path:
        tmp_path = file._tmp_path
        assert os.path.exists(tmp_path)
        del file
        assert not os.path.exists(tmp_path) 
        
def test_file_schema():
    """File fields should appear as {"type": "string", "format": "file"} inline, no $defs."""
    from typing import Optional, List

    class TestOutput(BaseAppOutput):
        video: Optional[File] = None
        images: List[File] = []

    schema = TestOutput.model_json_schema()
    # File should not appear in $defs (other types like OutputMeta may)
    defs = schema.get("$defs", {})
    assert "File" not in defs

    # Nullable file: anyOf [string+file, null]
    video_schema = schema["properties"]["video"]
    assert video_schema["anyOf"][0] == {"type": "string", "format": "file"}
    assert video_schema["anyOf"][1] == {"type": "null"}

    # Array of files: items is string+file
    images_schema = schema["properties"]["images"]
    assert images_schema["type"] == "array"
    assert images_schema["items"] == {"type": "string", "format": "file"}


def test_file_pydantic_validation():
    """File fields in pydantic models should accept strings, dicts, and File instances."""
    from typing import Optional

    class TestModel(BaseAppInput):
        video: Optional[File] = None

    # String coercion
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test")
        path = f.name

    try:
        m = TestModel(video=path)
        assert isinstance(m.video, File)
        assert m.video.uri == path
        assert m.video.path == os.path.abspath(path)

        # Dict coercion
        m2 = TestModel(video={"uri": path})
        assert isinstance(m2.video, File)
        assert m2.video.uri == path

        # File instance passthrough
        f_inst = File(path)
        m3 = TestModel(video=f_inst)
        assert m3.video is f_inst

        # None
        m4 = TestModel(video=None)
        assert m4.video is None
    finally:
        os.unlink(path)


def test_file_pydantic_serialization():
    """model_dump() should serialize File fields as dicts with uri/path keys."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test")
        path = f.name

    try:
        class TestModel(BaseAppInput):
            video: File

        m = TestModel(video=path)
        dumped = m.model_dump()
        assert isinstance(dumped["video"], dict)
        assert dumped["video"]["uri"] == path
        assert dumped["video"]["path"] == os.path.abspath(path)
        assert "content_type" in dumped["video"]
    finally:
        os.unlink(path)