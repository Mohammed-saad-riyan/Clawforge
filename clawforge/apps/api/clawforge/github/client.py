"""GitHub API client wrapper."""

import asyncio
import sys
from typing import Any
from functools import partial

from github import Github, Auth, Repository, PullRequest, GithubException


class GitHubClient:
    """Wrapper around PyGithub for async-friendly operations.

    Uses asyncio.to_thread() to run blocking PyGithub calls in a thread pool,
    preventing them from blocking the event loop.
    """

    def __init__(self, token: str, timeout: int = 30) -> None:
        self.token = token
        self.timeout = timeout
        self._client: Github | None = None

    @property
    def client(self) -> Github:
        """Lazy initialization of GitHub client."""
        if self._client is None:
            auth = Auth.Token(self.token)
            self._client = Github(auth=auth, timeout=self.timeout)
        return self._client

    async def create_repo(
        self,
        name: str,
        description: str = "",
        private: bool = True,
    ) -> Repository.Repository:
        """Create a new repository."""
        def _create():
            user = self.client.get_user()
            repo = user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=True,  # Initialize with README
            )
            return repo

        return await asyncio.wait_for(
            asyncio.to_thread(_create),
            timeout=60  # 60 second timeout for repo creation
        )

    async def get_repo(self, full_name: str) -> Repository.Repository:
        """Get repository by full name (owner/repo)."""
        return await asyncio.wait_for(
            asyncio.to_thread(self.client.get_repo, full_name),
            timeout=30
        )

    async def get_user(self) -> dict[str, Any]:
        """Get authenticated user info."""
        def _get_user():
            user = self.client.get_user()
            return {
                "login": user.login,
                "name": user.name,
                "avatar_url": user.avatar_url,
            }

        return await asyncio.wait_for(
            asyncio.to_thread(_get_user),
            timeout=30
        )

    async def create_branch(
        self,
        repo_name: str,
        branch_name: str,
        base_branch: str = "main",
    ) -> None:
        """Create a new branch from base branch."""
        def _create_branch():
            repo = self.client.get_repo(repo_name)
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=base_ref.object.sha,
            )

        await asyncio.wait_for(
            asyncio.to_thread(_create_branch),
            timeout=60
        )

    async def push_files(
        self,
        repo_name: str,
        files: list[dict[str, str]],
        branch: str = "main",
        commit_message: str = "Update files",
    ) -> None:
        """Push multiple files to repository.

        Tries the efficient Git Data API method first (single commit for all files).
        Falls back to creating files one-by-one if that fails (slower but more compatible).

        Args:
            repo_name: Full repository name (owner/repo)
            files: List of {"path": "file/path.dart", "content": "file content"}
            branch: Target branch
            commit_message: Commit message
        """
        try:
            # Try efficient batch method first
            await self._push_files_batch(repo_name, files, branch, commit_message)
        except Exception as e:
            error_str = str(e).lower()
            # If it's a permission/auth error, try the simple method
            if "401" in error_str or "403" in error_str or "bad credentials" in error_str:
                print(f"⚠️ Git Data API failed ({e}), falling back to file-by-file method...")
                sys.stdout.flush()
                await self._push_files_simple(repo_name, files, branch, commit_message)
            else:
                raise

    async def _push_files_batch(
        self,
        repo_name: str,
        files: list[dict[str, str]],
        branch: str,
        commit_message: str,
    ) -> None:
        """Push files using Git Data API (efficient, single commit)."""
        def _push():
            repo = self.client.get_repo(repo_name)

            # Get the current commit SHA for the branch
            ref = repo.get_git_ref(f"heads/{branch}")
            base_sha = ref.object.sha
            base_commit = repo.get_git_commit(base_sha)
            base_tree = base_commit.tree

            # Create blob for each file and build tree elements
            tree_elements = []
            for file_info in files:
                path = file_info["path"]
                content = file_info["content"]

                # Create a blob for the file content
                blob = repo.create_git_blob(content, "utf-8")
                tree_elements.append({
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob.sha,
                })

            # Create new tree with all files
            new_tree = repo.create_git_tree(tree_elements, base_tree)

            # Create new commit
            new_commit = repo.create_git_commit(
                message=commit_message,
                tree=new_tree,
                parents=[base_commit],
            )

            # Update the branch reference
            ref.edit(new_commit.sha)

        timeout = max(120, len(files) * 2)
        await asyncio.wait_for(
            asyncio.to_thread(_push),
            timeout=timeout
        )

    async def _push_files_simple(
        self,
        repo_name: str,
        files: list[dict[str, str]],
        branch: str,
        commit_message: str,
    ) -> None:
        """Push files one by one using Contents API (slower but more compatible)."""
        total = len(files)

        def _push():
            repo = self.client.get_repo(repo_name)

            for i, file_info in enumerate(files):
                path = file_info["path"]
                content = file_info["content"]

                # Log progress every 10 files
                if i % 10 == 0:
                    print(f"   📄 Pushing file {i+1}/{total}: {path[:50]}...")
                    sys.stdout.flush()

                try:
                    # Try to update existing file
                    existing = repo.get_contents(path, ref=branch)
                    if isinstance(existing, list):
                        existing = existing[0]
                    repo.update_file(
                        path=path,
                        message=f"{commit_message} ({i+1}/{total})",
                        content=content,
                        sha=existing.sha,
                        branch=branch,
                    )
                except Exception:
                    # Create new file
                    repo.create_file(
                        path=path,
                        message=f"{commit_message} ({i+1}/{total})",
                        content=content,
                        branch=branch,
                    )

            print(f"   ✅ All {total} files pushed successfully")
            sys.stdout.flush()

        # Simple method is slower - allow more time
        timeout = max(300, total * 5)  # 5 seconds per file
        await asyncio.wait_for(
            asyncio.to_thread(_push),
            timeout=timeout
        )

    async def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> PullRequest.PullRequest:
        """Create a pull request."""
        def _create_pr():
            repo = self.client.get_repo(repo_name)
            return repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
            )

        return await asyncio.wait_for(
            asyncio.to_thread(_create_pr),
            timeout=60
        )

    async def add_comment(
        self,
        repo_name: str,
        issue_number: int,
        body: str,
    ) -> None:
        """Add a comment to an issue or PR."""
        def _add_comment():
            repo = self.client.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            issue.create_comment(body)

        await asyncio.wait_for(
            asyncio.to_thread(_add_comment),
            timeout=30
        )
