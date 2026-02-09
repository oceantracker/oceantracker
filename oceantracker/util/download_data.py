import os
import requests
from pathlib import Path

import re

def download_hindcast_data_for_tutorials(data_path="./demo_hindcast"):
    """
    Download the tutorials from the GitHub repository if they do not exist locally.
    Wrapper for download_data_from_github.
    """
    # Check if data exists locally
    if not os.path.exists(data_path):
        print("Hindcast data not found locally. Downloading from GitHub...")
        
        # Download specific directory from repository
        repo_url = "https://github.com/oceantracker/oceantracker"
        download_data_from_github(repo_url, local_path=data_path, directory_path="tutorials_how_to/demo_hindcast") 
    else:
        print("Hindcast data found locally at", data_path)

def download_data_from_github(repo_url, local_path, directory_path=""):
    """
    Download a directory from a GitHub repository, handling Git LFS files.
    
    Args:
        repo_url (str): GitHub repository URL (e.g., "https://github.com/user/repo")
        local_path (str): Local path where to save the files
        directory_path (str): Specific directory in repo to download (e.g., "data" or "src/data")
    """
    def _is_lfs_pointer(content):
        """Check if content is a Git LFS pointer file"""
        try:
            text = content.decode('utf-8')
            # LFS pointer files start with "version https://git-lfs.github.com/spec/v1"
            return text.startswith('version https://git-lfs.github.com/spec/v1')
        except:
            return False
    
    def _parse_lfs_pointer(content):
        """Parse LFS pointer to extract OID"""
        try:
            text = content.decode('utf-8')
            # Extract the SHA256 OID from the pointer
            match = re.search(r'oid sha256:([a-f0-9]{64})', text)
            if match:
                return match.group(1)
        except:
            pass
        return None
    
    def _download_lfs_file(repo_url, directory_path, filename, oid):
        """Download actual LFS file from GitHub's media endpoint"""
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        # Construct the LFS media URL
        file_path = f"{directory_path}/{filename}" if directory_path else filename
        lfs_url = f"https://media.githubusercontent.com/media/{owner}/{repo}/main/{file_path}"
        
        try:
            response = requests.get(lfs_url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            return None
    
    def _collect_all_files(repo_url, directory_path=""):
        """Recursively collect all files to get total count and size"""
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{directory_path}"
        
        files = []
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            contents = response.json()
            
            for item in contents:
                if item['type'] == 'file':
                    files.append(item)
                elif item['type'] == 'dir':
                    subdir_path = f"{directory_path}/{item['name']}" if directory_path else item['name']
                    files.extend(_collect_all_files(repo_url, subdir_path))
            
        except requests.exceptions.RequestException:
            pass
        
        return files
    
    def _download_files_with_progress(repo_url, local_path, directory_path="", file_counter=None, all_files=None):
        """Download files with progress tracking, handling LFS files"""
        if file_counter is None:
            file_counter = {'count': 0}
        if all_files is None:
            all_files = _collect_all_files(repo_url, directory_path)
        
        # Extract owner and repo name from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{directory_path}"
        
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            contents = response.json()
            
            # Create local directory if it doesn't exist
            Path(local_path).mkdir(parents=True, exist_ok=True)
            
            total_files = len(all_files)
            total_size = sum(file.get('size', 0) for file in all_files)
            downloaded_size = sum(file.get('size', 0) for file in all_files[:file_counter['count']])
            
            for item in contents:
                item_path = os.path.join(local_path, item['name'])
                
                if item['type'] == 'file':
                    file_counter['count'] += 1
                    current_file_size = item.get('size', 0)
                    
                    # Update progress display
                    progress_str = f"Downloading file: {file_counter['count']}/{total_files} - {downloaded_size/(1024*1024):.1f}MB/{total_size/(1024*1024):.1f}MB - Current file: {item['name']}"
                    print(f"\r{progress_str}", end="", flush=True)
                    
                    # Download file
                    file_response = requests.get(item['download_url'])
                    file_response.raise_for_status()
                    file_content = file_response.content
                    
                    # Check if this is an LFS pointer file
                    if _is_lfs_pointer(file_content):
                        oid = _parse_lfs_pointer(file_content)
                        if oid:
                            # Update progress to show LFS detection
                            lfs_progress_str = f"Downloading file: {file_counter['count']}/{total_files} - {downloaded_size/(1024*1024):.1f}MB/{total_size/(1024*1024):.1f}MB - Current file: {item['name']} (LFS detected, fetching actual content...)"
                            print(f"\r{lfs_progress_str}", end="", flush=True)
                            
                            lfs_content = _download_lfs_file(repo_url, directory_path, item['name'], oid)
                            if lfs_content is not None:
                                file_content = lfs_content
                                current_file_size = len(lfs_content)
                    
                    # Write file to disk
                    with open(item_path, 'wb') as f:
                        f.write(file_content)
                    
                    downloaded_size += current_file_size
                    
                elif item['type'] == 'dir':
                    # Recursively download subdirectory
                    subdir_path = f"{directory_path}/{item['name']}" if directory_path else item['name']
                    _download_files_with_progress(repo_url, item_path, subdir_path, file_counter, all_files)
            
        except requests.exceptions.RequestException as e:
            print(f"\nError downloading from GitHub: {e}")
            return False
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return False
        
        return True
    
    # Start download with progress tracking
    success = _download_files_with_progress(repo_url, local_path, directory_path)
    if success:
        print(f"\nSuccessfully downloaded directory to: {local_path}")
    
    return success

# Usage example
# if __name__ == "__main__":
#     # Check if data exists locally
#     data_path = "./local_data"
    
#     if not os.path.exists(data_path):
#         print("Data not found locally. Downloading from GitHub...")
        
#         # Download specific directory from repository
#         repo_url = "https://github.com/username/repository"
#         download_data_from_github(repo_url, data_path, "data")  # Downloads the 'data' directory
#     else:
#         print("Data already exists locally!")