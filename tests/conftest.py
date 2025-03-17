import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import tempfile


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_text_file():
    """Create a temporary text file for testing"""
    content = "This is a sample text file for testing summarization functionality."

    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(content)

    # Return the path to the file
    yield path

    # Clean up the file after the test, only if it exists
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass  # File already deleted, nothing to do


@pytest.fixture
def mock_ollama_response(monkeypatch):
    """Mock the Ollama API response"""

    def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {"response": "This is a mock summary."}

            def raise_for_status(self):
                pass

        return MockResponse()

    # Patch the requests.post method
    import requests

    monkeypatch.setattr(requests, "post", mock_post)
