""
Git Repository Manager using GitPython for easy repository management.
Supports both regular and sparse checkouts with automated updates.
"""

from typing import Optional, List
from pathlib import Path
from git import Repo, GitCommandError
import os


class GitRepoManager:
    """Manages git repository cloning and updating operations using GitPython."""
    
    def __init__(self, repo_url: str):
        """
        Initialize GitRepoManager with a repository URL.
        
        Args:
            repo_url (str): The URL of the git repository to clone
        """
        self.repo_url = repo_url
    
    def clone_or_update(self, 
                       target_path: str,
                       branch: str = 'main',
                       sparse: bool = False,
                       sparse_paths: Optional[List[str]] = None) -> Path:
        """
        Clone a git repository or update if it already exists.
        
        Args:
            target_path (str): Path where the repository should be cloned/updated
            branch (str, optional): Branch to checkout. Defaults to 'main'
            sparse (bool, optional): Whether to perform sparse checkout. Defaults to False
            sparse_paths (List[str], optional): List of paths to include in sparse checkout
                                              Required if sparse=True
        
        Returns:
            Path: Path object pointing to the repository
        
        Raises:
            ValueError: If sparse is True but sparse_paths is None or empty
            GitCommandError: If any git operation fails
        """
        target_path = Path(target_path).resolve()
        
        if sparse and not sparse_paths:
            raise ValueError("sparse_paths must be provided when sparse=True")
        
        if target_path.exists() and (target_path / '.git').exists():
            return self._update_repo(target_path, branch)
        else:
            return self._clone_repo(target_path, branch, sparse, sparse_paths)

    def _update_repo(self, target_path: Path, branch: str) -> Path:
        """
        Update existing repository with improved error handling.
        
        Args:
            target_path (Path): Path to the existing repository
            branch (str): Branch to update and checkout
            
        Returns:
            Path: Path to the updated repository
            
        Raises:
            GitCommandError: If any git operation fails
        """
        try:
            repo = Repo(target_path)
            origin = repo.remotes.origin
            
            # Fetch latest changes
            origin.fetch()
            
            # Store current branch
            current = repo.active_branch
            
            # Reset any local changes
            repo.git.reset('--hard')
            repo.git.clean('-fd')
            
            # Check if branch exists locally
            if branch in repo.heads:
                local_branch = repo.heads[branch]
            else:
                # Create local branch tracking remote
                local_branch = repo.create_head(branch, origin.refs[branch])
            
            # Set up tracking and checkout
            local_branch.set_tracking_branch(origin.refs[branch])
            local_branch.checkout()
            
            # Pull with specific options for better reliability
            repo.git.pull('--ff-only', '--verbose')
            
            return target_path
            
        except GitCommandError as e:
            # Add more context to the error
            raise GitCommandError(
                f"Failed to update repository at {target_path}. "
                f"Original error: {e.command}",
                e.status,
                e.stderr
            )

    def _clone_repo(self, 
                    target_path: Path,
                    branch: str,
                    sparse: bool,
                    sparse_paths: Optional[List[str]]) -> Path:
        """
        Clone repository (either sparse or regular).
        
        Args:
            target_path (Path): Where to clone the repository
            branch (str): Branch to clone
            sparse (bool): Whether to perform sparse checkout
            sparse_paths (Optional[List[str]]): Paths to include in sparse checkout
            
        Returns:
            Path: Path to the cloned repository
            
        Raises:
            GitCommandError: If clone operation fails
        """
        target_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if sparse:
                return self._sparse_clone(target_path, branch, sparse_paths)
            else:
                return self._regular_clone(target_path, branch)
        except GitCommandError as e:
            raise GitCommandError(
                f"Failed to clone repository to {target_path}. "
                f"Original error: {e.command}",
                e.status,
                e.stderr
            )
    
    def _regular_clone(self, target_path: Path, branch: str) -> Path:
        """
        Perform a regular git clone.
        
        Args:
            target_path (Path): Where to clone the repository
            branch (str): Branch to clone
            
        Returns:
            Path: Path to the cloned repository
        """
        Repo.clone_from(
            self.repo_url,
            str(target_path),
            branch=branch,
            single_branch=True
        )
        return target_path
    
    def _sparse_clone(self, target_path: Path, branch: str, sparse_paths: List[str]) -> Path:
        """
        Perform a sparse checkout.
        
        Args:
            target_path (Path): Where to clone the repository
            branch (str): Branch to clone
            sparse_paths (List[str]): Paths to include in sparse checkout
            
        Returns:
            Path: Path to the cloned repository
        """
        # Initialize repo
        repo = Repo.init(target_path)
        
        # Add remote
        origin = repo.create_remote('origin', self.repo_url)
        
        # Configure sparse checkout
        config = repo.config_writer()
        config.set_value('core', 'sparseCheckout', 'true')
        config.release()
        
        # Write sparse-checkout patterns
        sparse_file = target_path / '.git' / 'info' / 'sparse-checkout'
        sparse_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_file.write_text('\n'.join(sparse_paths))
        
        # Fetch and checkout
        origin.fetch(branch)
        repo.create_head(branch, origin.refs[branch])
        repo.heads[branch].checkout()
        
        return target_path

    def __repr__(self) -> str:
        """String representation of the GitRepoManager."""
        return f"GitRepoManager(repo_url='{self.repo_url}')"
