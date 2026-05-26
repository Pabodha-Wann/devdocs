import os
import tempfile
import shutil
from git import Repo
from app.ingestion import extract_code_files, is_binary_file

# URL of your repo
REPO_URL = ""

# Clone the repo
temp_dir = tempfile.mkdtemp(prefix="test_repo_")

try:
    print(f"Cloning {REPO_URL}...")
    Repo.clone_from(REPO_URL, temp_dir, depth=1)
    print(f"Cloned to {temp_dir}\n")
    
    # Extract files
    print("Extracting files...")
    documents = extract_code_files(temp_dir)
    
    print(f"✅ Found {len(documents)} files\n")
    
    # Group by folder
    folders = {}
    for doc in documents:
        source = doc.metadata["source"]
        folder = "/".join(source.split("/")[:-1])
        
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(source)
    
    # Print results
    print("Files by folder:\n")
    for folder in sorted(folders.keys()):
        files = folders[folder]
        print(f"📁 {folder}/ ({len(files)} files)")
        for file in files[:3]:  # Show first 3
            print(f"   - {file}")
        if len(files) > 3:
            print(f"   ... and {len(files) - 3} more")
    
    # Check what's in src/models and src/utils
    print("\n" + "="*60)
    print("Checking src/models and src/utils directly:\n")
    
    src_models = os.path.join(temp_dir, "src", "models")
    src_utils = os.path.join(temp_dir, "src", "utils")
    
    if os.path.exists(src_models):
        print(f"📁 {src_models} EXISTS")
        for root, dirs, files in os.walk(src_models):
            level = root.replace(src_models, "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files[:5]:
                size = os.path.getsize(os.path.join(root, file))
                is_binary = is_binary_file(os.path.join(root, file))
                print(f"{subindent}{file} ({size} bytes) - Binary: {is_binary}")
    else:
        print(f"❌ {src_models} DOES NOT EXIST")
    
    print()
    
    if os.path.exists(src_utils):
        print(f"📁 {src_utils} EXISTS")
        for root, dirs, files in os.walk(src_utils):
            level = root.replace(src_utils, "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files[:5]:
                size = os.path.getsize(os.path.join(root, file))
                is_binary = is_binary_file(os.path.join(root, file))
                print(f"{subindent}{file} ({size} bytes) - Binary: {is_binary}")
    else:
        print(f"❌ {src_utils} DOES NOT EXIST")

finally:
    print("\nCleaning up...")
    shutil.rmtree(temp_dir)
    print("Done!")