import os
import pytest
import io
from fastapi import UploadFile
from app.services.file_service import save_upload_file, cleanup_file


class MockUploadFile:
    def __init__(self, content):
        self.file = io.BytesIO(content)


@pytest.mark.asyncio
async def test_save_upload_file():
    """Test saving an uploaded file"""
    # Create a mock file
    content = b"Test file content"
    mock_file = MockUploadFile(content)

    # Call the function
    file_path = await save_upload_file(mock_file, "test.txt")

    try:
        # Verify the file exists and has the correct content
        assert os.path.exists(file_path)
        with open(file_path, "rb") as f:
            saved_content = f.read()
        assert saved_content == content
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)


def test_cleanup_file(sample_text_file):
    """Test file cleanup function"""
    # Verify the file exists before cleanup
    assert os.path.exists(sample_text_file)

    # Call the cleanup function
    result = cleanup_file(sample_text_file)

    # Verify results
    assert result is True
    assert not os.path.exists(sample_text_file)
