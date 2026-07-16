from exceptions import InvalidRepositoryError
import tempfile
import os
import pytest
from app.ingestion import is_binary_file
from langchain_core.documents import Document
from app.ingestion import chunk_documents
from app.ingestion import clone_repository
from app.ingestion import generate_directory_tree
from app.ingestion import extract_code_files
from app.ingestion import extract_code_files

def test_is_binary_file_with_text():
    # Create a temperary test file
    with tempfile.NamedTemporaryFile(mode='w',delete=False,suffix='.py') as f:
        f.write("print('Hello World')")
        temp_path = f.name

    try:
        assert is_binary_file(temp_path) is False
    finally:
        os.remove(temp_path)


def test_is_binary_file_with_binary():
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.png') as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR') # Fake PNG header
        temp_path = f.name

    try:
        assert is_binary_file(temp_path) is True
    finally:
        os.remove(temp_path)



def test_clone_repository_invalid_url():
    # Verify that an empty string properly raises your custom exception
    with pytest.raises(InvalidRepositoryError) as exc_info:
        clone_repository("")
    assert "Repository URL cannot be empty" in str(exc_info.value)
    
    # Verify that non-string parameters raise the type check validation error
    with pytest.raises(InvalidRepositoryError) as exc_info:
        clone_repository(None)
    assert "Repository URL must be a string" in str(exc_info.value)


def test_chunk_documents_metadata(monkeypatch):
    # Mock the required config variables so the test runs in isolation
    monkeypatch.setattr("app.ingestion.CHUNK_SIZE", 2000)
    monkeypatch.setattr("app.ingestion.CHUNK_OVERLAP", 200)
    monkeypatch.setattr("app.ingestion.EXTENSION_TO_LANGUAGE", {".tsx": "ts"})
    
    # Create a dummy extracted document
    mock_doc = Document(
        page_content="export default function AdminPage() { return <div>Admin</div> }",
        metadata={"source": "frontend/src/pages/AdminPage.tsx"}
    )
    
    # Run the chunking processor
    repo_url = "https://github.com/user/repo"
    chunks = chunk_documents([mock_doc], url=repo_url)
    
    assert len(chunks) > 0
    first_chunk = chunks[0]
    
    # Crucial assertions verifying your folder path fixes work perfectly
    assert first_chunk.metadata["folder"] == "frontend/src/pages"
    assert first_chunk.metadata["file_name"] == "AdminPage.tsx"
    assert first_chunk.metadata["depth"] == 3
    assert first_chunk.metadata["repo_url"] == repo_url
    assert "FILE: frontend/src/pages/AdminPage.tsx" in first_chunk.page_content




def test_generate_directory_tree():
    # Create a temporary directory structure acting as a mock repository
    with tempfile.TemporaryDirectory() as temp_repo:
        # Create a file in root
        with open(os.path.join(temp_repo, "README.md"), "w") as f:
            f.write("# Dummy project")
            
        # Create a nested folder structure
        src_dir = os.path.join(temp_repo, "src")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "App.jsx"), "w") as f:
            f.write("function App() {}")
            
        # Run your tree generator
        tree_output = generate_directory_tree(temp_repo)
        
        # Verify the structure text visually formats identically to your plan
        assert "[REPOSITORY DIRECTORY STRUCTURE AND FILE TREE]" in tree_output
        assert "[ROOT]" in tree_output
        assert "README.md" in tree_output
        assert "[DIR] src/" in tree_output
        assert "App.jsx" in tree_output




def test_extract_code_files_ignores_blocked_directories(monkeypatch):
    # Setup blocked configuration for testing
    monkeypatch.setattr("app.ingestion.BLOCKED_DIRS", {"node_modules", ".git"})
    monkeypatch.setattr("app.ingestion.MAX_FILE_SIZE", 500_000)
    monkeypatch.setattr("app.ingestion.BINARY_EXTENSIONS", set())
    monkeypatch.setattr("app.ingestion.IGNORED_FILES", set())

    with tempfile.TemporaryDirectory() as temp_repo:
        # Create a valid file in the root
        with open(os.path.join(temp_repo, "main.py"), "w") as f:
            f.write("print('hello')")

        # Create a nested file inside a forbidden directory string path
        blocked_folder = os.path.join(temp_repo, "node_modules", "package")
        os.makedirs(blocked_folder)
        with open(os.path.join(blocked_folder, "index.js"), "w") as f:
            f.write("console.log('leak')")

        docs = extract_code_files(temp_repo)
        
        # Verify main.py is indexed, but index.js is completely ignored
        sources = [doc.metadata["source"] for doc in docs]
        assert "main.py" in sources
        assert "node_modules/package/index.js" not in sources 
        assert "node_modules\\package\\index.js" not in sources




def test_extract_code_files_skips_large_files(monkeypatch):
    # Set MAX_FILE_SIZE very low for the test context (10 bytes)
    monkeypatch.setattr("app.ingestion.MAX_FILE_SIZE", 10)
    monkeypatch.setattr("app.ingestion.BLOCKED_DIRS", set())
    monkeypatch.setattr("app.ingestion.BINARY_EXTENSIONS", set())
    monkeypatch.setattr("app.ingestion.IGNORED_FILES", set())

    with tempfile.TemporaryDirectory() as temp_repo:
        # File 1: Small file (should be extracted)
        small_file = os.path.join(temp_repo, "small.py")
        with open(small_file, "w") as f:
            f.write("abc")  # 3 bytes

        # File 2: Large file exceeding our 10-byte cap (should be skipped)
        large_file = os.path.join(temp_repo, "large.py")
        with open(large_file, "w") as f:
            f.write("This string is definitely longer than ten bytes!")

        docs = extract_code_files(temp_repo)
        
        # We expect 2 documents: the [DIRECTORY_TREE.txt] document + small.py
        # large.py must be missing from the results
        assert len(docs) == 2
        
        sources = [doc.metadata["source"] for doc in docs]
        assert "small.py" in sources
        assert "large.py" not in sources