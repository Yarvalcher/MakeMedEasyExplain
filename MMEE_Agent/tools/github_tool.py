import os
import json
import base64
import urllib.request
import urllib.error

def get_github_pat() -> str:
    """Retrieves GITHUB_PAT prioritizing Google Secret Manager, falling back to local environment."""
    pat = os.getenv("GITHUB_PAT")
    if pat:
        return pat
        
    try:
        from google.cloud import secretmanager
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if project_id:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/GITHUB_PAT/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8").strip()
    except Exception:
        pass
    return ""

def commit_to_github(filename: str, content: str) -> str:
    """Commits a markdown file directly to the GitHub repository wiki under knowledge_base/.
    
    Args:
        filename: Name of the markdown file (e.g. 't_cell.md'). Must be a simple filename.
        content: The text content of the markdown file.
    """
    pat = get_github_pat()
    if not pat:
        return "Error: GITHUB_PAT token not found in Secret Manager or local environment variables."
        
    repo = os.getenv("GITHUB_REPO", "Yarvalcher/MakeMedEasyExplain")
    
    # Security Guardrails: Enforce flat directory mapping and markdown extension locks
    if not filename.endswith(".md") or "/" in filename or "\\" in filename:
        return "Error: Security violation. Filename must be a simple .md filename without directories."
        
    url = f"https://api.github.com/repos/{repo}/contents/knowledge_base/{filename}"
    
    # 1. Fetch file if it exists to get the current blob SHA
    sha = None
    get_req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {pat}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MakeMedEasyExplain/1.0"
        }
    )
    try:
        with urllib.request.urlopen(get_req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            sha = res_data.get("sha")
    except urllib.error.HTTPError as e:
        # 404 is normal for new files, other codes indicate API errors
        if e.code != 404:
            return f"Error checking file status on GitHub: {e.reason} (HTTP {e.code})"
    except Exception as e:
        return f"Error connecting to GitHub API: {e}"
        
    # 2. Base64 encode the markdown content
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    # 3. Formulate payload
    payload = {
        "message": f"Sync wiki: {filename}",
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
        
    put_req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"token {pat}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "MakeMedEasyExplain/1.0"
        },
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(put_req, timeout=10) as response:
            return f"Successfully committed {filename} to GitHub wiki."
    except Exception as e:
        return f"Failed to commit file to GitHub: {e}"

def sync_wiki_from_github(local_kb_dir: str) -> str:
    """Fetches all markdown files from the GitHub repository contents and synchronizes them to the local directory.
    
    Args:
        local_kb_dir: Path to the local knowledge base directory.
    """
    pat = get_github_pat()
    if not pat:
        return "Skip sync: GITHUB_PAT not configured."
        
    repo = os.getenv("GITHUB_REPO", "Yarvalcher/MakeMedEasyExplain")
    url = f"https://api.github.com/repos/{repo}/contents/knowledge_base"
    
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"token {pat}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MakeMedEasyExplain/1.0"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            contents = json.loads(response.read().decode("utf-8"))
            if not isinstance(contents, list):
                return "Failed sync: GitHub returned unexpected format."
                
            os.makedirs(local_kb_dir, exist_ok=True)
            sync_count = 0
            for item in contents:
                if item.get("type") == "file" and item.get("name", "").endswith(".md"):
                    file_name = item["name"]
                    download_url = item.get("download_url")
                    if download_url:
                        # Fetch the file content
                        with urllib.request.urlopen(download_url, timeout=5) as file_resp:
                            file_content = file_resp.read()
                            target_path = os.path.join(local_kb_dir, file_name)
                            with open(target_path, "wb") as f:
                                f.write(file_content)
                            sync_count += 1
            return f"Successfully synchronized {sync_count} files from GitHub wiki."
    except Exception as e:
        return f"Wiki synchronization failed: {e}"

