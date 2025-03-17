import io
import pytest
from app.core.enums import FileType


def test_summarize_text_file(client, sample_text_file, mock_ollama_response):
    """Test the file summarization endpoint with a text file"""
    # Open the sample file
    with open(sample_text_file, "rb") as f:
        file_content = f.read()

    # Create a file-like object for the test client
    test_file = io.BytesIO(file_content)

    # Make the API call with the file_name parameter that's required
    response = client.post(
        "/summarize",
        files={"file": ("sample.txt", test_file, "text/plain")},
        data={
            "file_type": FileType.TEXT.value,
            "file_name": "sample.txt",
            "language": "en",
        },
    )

    # For debugging
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content}")

    # Verify the response
    assert response.status_code == 200


def test_direct_text_summarization(client, mock_ollama_response):
    """Test the direct text summarization endpoint"""
    response = client.post(
        "/summarize/text", data={"text": "This is a test text to summarize."}
    )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["file_type"] == FileType.TEXT
