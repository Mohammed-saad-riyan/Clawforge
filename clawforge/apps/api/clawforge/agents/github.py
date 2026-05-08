"""GitHub agent - handles all GitHub operations.

The GitHubAgent:
1. Creates repositories using user's PAT token
2. Pushes generated files to branches
3. Creates pull requests for review
4. Uses the token provided in each request (not global config)
"""

from typing import Any

from clawforge.agents.base import AgentResult, BaseAgent
from clawforge.github.client import GitHubClient


class GitHubAgent(BaseAgent):
    """Handles GitHub operations: repo creation, pushes, branches, PRs.

    Token is provided per-request, allowing different users to use their own tokens.
    No LLM needed - all operations are direct GitHub API calls.
    """

    name = "github"
    description = "Manages GitHub repositories, branches, and pull requests"

    def _get_client(self, token: str) -> GitHubClient:
        """Get GitHub client with provided token."""
        if not token:
            raise ValueError("GitHub token is required")
        return GitHubClient(token=token)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute a GitHub operation."""
        action = input_data.get("action", "")
        token = input_data.get("token", "")

        if not token:
            return AgentResult(
                success=False,
                output=None,
                error="GitHub token is required for all operations"
            )

        try:
            match action:
                case "create_repo":
                    result = await self._create_repo(input_data, token)
                case "push_files":
                    result = await self._push_files(input_data, token)
                case "create_branch":
                    result = await self._create_branch(input_data, token)
                case "create_pr":
                    result = await self._create_pr(input_data, token)
                case "get_user":
                    result = await self._get_user(token)
                case _:
                    return AgentResult(
                        success=False, output=None, error=f"Unknown action: {action}"
                    )

            return AgentResult(success=True, output=result, cost_cents=0, tokens_used=0)
        except Exception as e:
            error_msg = str(e)
            original_error = error_msg  # Keep original for logging

            # Make error messages more user-friendly while keeping details
            if "401" in error_msg or "Bad credentials" in error_msg:
                error_msg = f"Invalid GitHub token. Please check your Personal Access Token has 'repo' scope. (Original: {original_error[:200]})"
            elif "403" in error_msg:
                error_msg = f"Permission denied. Your token may not have required permissions. Ensure 'repo' scope is enabled. (Original: {original_error[:200]})"
            elif "404" in error_msg:
                error_msg = f"Repository not found or you don't have access: {original_error[:200]}"
            elif "422" in error_msg:
                if "already exists" in error_msg.lower():
                    error_msg = "Repository or branch already exists."
                else:
                    error_msg = f"GitHub validation error: {original_error[:200]}"
            elif "timeout" in error_msg.lower():
                error_msg = f"GitHub API timed out. Please try again. (Original: {original_error[:200]})"

            return AgentResult(success=False, output=None, error=error_msg)

    async def _get_user(self, token: str) -> dict[str, Any]:
        """Get authenticated user info."""
        client = self._get_client(token)
        return await client.get_user()

    async def _create_repo(self, data: dict[str, Any], token: str) -> dict[str, str]:
        """Create a new GitHub repository."""
        client = self._get_client(token)

        name = data.get("name", "")
        description = data.get("description", "")
        private = data.get("private", False)

        if not name:
            raise ValueError("Repository name is required")

        repo = await client.create_repo(
            name=name,
            description=description,
            private=private,
        )

        # Get the user's login to construct full_name
        user_info = await client.get_user()

        return {
            "repo_url": repo.html_url,
            "clone_url": repo.clone_url,
            "name": repo.name,
            "full_name": f"{user_info['login']}/{repo.name}",
        }

    async def _push_files(self, data: dict[str, Any], token: str) -> dict[str, str]:
        """Push generated files to repository."""
        client = self._get_client(token)

        repo_name = data.get("repo_name", "")
        files = data.get("files", [])
        branch = data.get("branch", "main")
        message = data.get("message", "Add generated files")

        if not repo_name:
            raise ValueError("Repository name is required")
        if not files:
            raise ValueError("No files to push")

        await client.push_files(
            repo_name=repo_name,
            files=files,
            branch=branch,
            commit_message=message,
        )

        return {
            "status": "pushed",
            "repo_name": repo_name,
            "branch": branch,
            "files_count": len(files),
        }

    async def _create_branch(self, data: dict[str, Any], token: str) -> dict[str, str]:
        """Create a new branch."""
        client = self._get_client(token)

        repo_name = data.get("repo_name", "")
        branch_name = data.get("branch_name", "")
        base_branch = data.get("base_branch", "main")

        if not repo_name:
            raise ValueError("Repository name is required")
        if not branch_name:
            raise ValueError("Branch name is required")

        try:
            await client.create_branch(
                repo_name=repo_name,
                branch_name=branch_name,
                base_branch=base_branch,
            )
        except Exception as e:
            # Branch might already exist, check if it's that error
            if "already exists" in str(e).lower() or "Reference already exists" in str(e):
                return {
                    "branch_name": branch_name,
                    "base_branch": base_branch,
                    "status": "already_exists",
                }
            raise

        return {
            "branch_name": branch_name,
            "base_branch": base_branch,
            "status": "created",
        }

    async def _create_pr(self, data: dict[str, Any], token: str) -> dict[str, str]:
        """Create a pull request."""
        client = self._get_client(token)

        repo_name = data.get("repo_name", "")
        title = data.get("title", "")
        body = data.get("body", "")
        head = data.get("head", "")
        base = data.get("base", "main")

        if not repo_name:
            raise ValueError("Repository name is required")
        if not title:
            raise ValueError("PR title is required")
        if not head:
            raise ValueError("Head branch is required")

        pr = await client.create_pull_request(
            repo_name=repo_name,
            title=title,
            body=body,
            head=head,
            base=base,
        )

        return {
            "pr_url": pr.html_url,
            "pr_number": pr.number,
            "status": "created",
        }
