from pathlib import Path
import shutil
from git import Repo
from typing import Optional, Dict
import tempfile
import subprocess
from datetime import datetime, timezone
import logging

# Create a module-level logger
logger = logging.getLogger(__name__)

def get_repo_metadata(repo_path: Path) -> Dict:
    """Get essential metadata about the repository state for reproducibility.
    
    Args:
        repo_path: Path to the local repository
        
    Returns:
        Dict containing:
            - commit_time: ISO formatted UTC timestamp of when the commit was made
            - remote_url: URL of the origin remote
            - sha: full commit hash
            - branch: current branch name or HEAD if detached
    """
    repo = Repo(repo_path)
    commit = repo.head.commit
    
    # Get remote URL
    remote_url = repo.remotes.origin.url
    if remote_url.endswith('.git'):
        remote_url = remote_url[:-4]
    
    # Get current branch or HEAD if detached
    try:
        current_branch = repo.active_branch.name
    except TypeError:  # HEAD is detached
        current_branch = 'HEAD'
    
    return {
        "commit_time": commit.committed_datetime.isoformat(),
        "remote_url": remote_url,
        "sha": commit.hexsha,
        "branch": current_branch
    }

def get_git_blame_info(repo_path: Path, file_path: Path, line_number: int) -> dict:
    """Get git blame information for a specific line."""
    repo = Repo(repo_path)
    blame = repo.blame('HEAD', str(file_path), L=f"{line_number},{line_number}")[0]
    commit = blame[0]
    return {
        "commit": commit.hexsha,
        "author": commit.author.name,
        "author_email": commit.author.email,
        "date": commit.authored_datetime.isoformat(),
        "summary": commit.summary
    }

def get_head_sha(remote_url: str, branch: str = None) -> str:
    """Get the HEAD SHA of a branch."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Repo.clone_from(
            remote_url,
            temp_dir,
            branch=branch,
            depth=1
        )
        return repo.head.commit.hexsha

def prepare_repository(remote_url: str, branch: str, head_sha: str, lean_data: Path) -> Optional[Path]:
    """Clone repository at specific commit into lean-data directory.
    
    Args:
        remote_url: Git remote URL (HTTPS or SSH)
        branch: Branch name
        head_sha: Commit SHA to checkout
        lean_data: Base directory for checkouts
    
    Returns:
        Path to checked out repository or None if failed
    """
    if head_sha is None:
        head_sha = get_head_sha(remote_url, branch)
    
    checkout_path = lean_data / head_sha
    
    # If directory exists and has correct commit checked out, we're done
    if checkout_path.exists():
        try:
            repo = Repo(checkout_path)
            if repo.head.commit.hexsha == head_sha:
                logger.info(f"Repository already exists at correct commit {head_sha}")
                return checkout_path
        except Exception:
            pass
    
    # Clean up if directory exists but wrong commit
    if checkout_path.exists():
        shutil.rmtree(checkout_path)
    
    try:
        # Clone repository
        logger.info(f"Cloning {remote_url} branch {branch}...")
        repo = Repo.clone_from(
            remote_url,
            checkout_path,
            branch=branch,
            single_branch=True
        )
        
        # Checkout specific commit
        logger.info(f"Checking out {head_sha}...")
        repo.git.checkout(head_sha)
        
        return checkout_path
        
    except Exception as e:
        logger.error(f"Error preparing repository: {e}")
        # Clean up on failure
        if checkout_path.exists():
            shutil.rmtree(checkout_path)
        return None

def get_default_branch(repo_path: Path) -> str:
    """Get the default branch of the repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return result.stdout.strip() 