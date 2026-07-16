from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

# Create a test client 
client = TestClient(app)

def test_ingest_repo_invalid_url():
    """Test that the API correctly blocks bad URLs without calling the database."""
    
    response = client.post("/api/ingest-repo", json={"url": "not-a-github-url"})
    
    # We expect a 422 Unprocessable Entity error because of our Pydantic validation
    assert response.status_code == 422
    assert "Invalid GitHub URL" in response.text

# We use @patch to intercept 'clone_and_embed' so it DOES NOT actually run!
@patch("app.routes.clone_and_embed")
def test_ingest_repo_success(mock_clone_and_embed):
    """Test that a valid URL returns success."""
    
    # Force the mock function
    mock_clone_and_embed.return_value = (5, 20) # (files_scanned, chunks_created)
    
    response = client.post(
        "/api/ingest-repo", 
        json={"url": "https://github.com/owner/repo"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["files_scanned"] == 5
    assert data["chunks_created"] == 20
    
    # Verify that our mocked function was called with the correct URL
    mock_clone_and_embed.assert_called_once_with("https://github.com/owner/repo")


def test_chat_invalid_messages():
    """Test that the API rejects invalid chat payloads (like wrong roles or empty messages)."""
    
    # Send a message with a bad role ('alien' instead of 'user'/'assistant')
    response = client.post(
        "/api/chat", 
        json={
            "repo_url": "https://github.com/owner/repo",
            "messages": [{"role": "alien", "content": "take me to your leader"}]
        }
    )
    
    # Expect a validation error
    assert response.status_code == 422
    assert "Role must be 'user' or 'assistant'" in response.text


@patch("app.routes.llm.generate_answer")
@patch("app.routes.search_codebase")
def test_chat_success(mock_search_codebase, mock_generate_answer):
    """Test a successful chat interaction with mocked DB and LLM."""
    
    # Setup the fake database response
    mock_search_codebase.return_value = [
        {"source": "src/App.jsx", "content": "function App() {}"}
    ]
    
    # Setup the fake LLM response
    mock_generate_answer.return_value = "This is a fake AI answer based on App.jsx!"
    
    # Execution: Call our API
    response = client.post(
        "/api/chat", 
        json={
            "repo_url": "https://github.com/owner/repo",
            "messages": [{"role": "user", "content": "What is in App.jsx?"}]
        }
    )
    
    # 4. Assertions: Did our API return what we expect?
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert data["answer"] == "This is a fake AI answer based on App.jsx!"
    
    # Check that our sources passed correctly
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source"] == "src/App.jsx"
    
    # Verify that code actually passed the correct user question to the database
    mock_search_codebase.assert_called_once_with(
        query="What is in App.jsx?", 
        repo_url="https://github.com/owner/repo"
    )