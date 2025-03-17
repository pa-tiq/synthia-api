import pytest
from app.services.summarization.text import generate_text_summary


def test_generate_text_summary(mock_ollama_response):
    """Test the text summarization function"""
    # Call the function
    summary = generate_text_summary("This is a test text to summarize.")

    # Verify the result
    assert summary == "This is a mock summary."


def test_generate_text_summary_with_language(mock_ollama_response):
    """Test the text summarization with a specific language"""
    # Call the function with a language parameter
    summary = generate_text_summary("This is a test text to summarize.", "pt-br")

    # In a real test, you might verify that the language was passed to the model
    # Here we just check that it returns the mock summary
    assert summary == "This is a mock summary."
