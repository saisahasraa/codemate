"""
This module provides a unified interface for interacting with different Git servers.
It uses a base class and specific client implementations for each server.
"""

import os
from abc import ABC, abstractmethod
import requests

class BaseGitClient(ABC):
    """Abstract base class for all Git server clients."""

    def __init__(self, token: str):
        """Initializes the client with a personal access token."""
        self.token = token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    @abstractmethod
    def fetch_pr_details(self, owner: str, repo: str, pr_number: int):
        """Fetches the details and file changes of a pull request."""
        pass

    @abstractmethod
    def post_review_comment(self, owner: str, repo: str, pr_number: int, comment: str):
        """Posts a general comment on a pull request."""
        pass

    @abstractmethod
    def post_inline_comment(self, owner: str, repo: str, pr_number: int, file_path: str, line_number: int, comment: str):
        """Posts an inline comment on a specific line of a file in a pull request."""
        pass

class GitHubClient(BaseGitClient):
    """Client for interacting with GitHub's API."""
    
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        """Initializes the GitHub client with a token."""
        super().__init__(token)
        # GitHub uses 'token' for Authorization header
        self.headers['Authorization'] = f"token {self.token}"

    def fetch_pr_details(self, owner: str, repo: str, pr_number: int):
        """Fetches PR details and file changes from GitHub."""
        try:
            pr_url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
            files_url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            
            pr_response = requests.get(pr_url, headers=self.headers)
            pr_response.raise_for_status()
            pr_data = pr_response.json()

            files_response = requests.get(files_url, headers=self.headers)
            files_response.raise_for_status()
            files_data = files_response.json()
            
            # Extract the diffs from the files data
            file_changes = {}
            for file in files_data:
                # GitHub's API provides a 'raw_url' to the file, and a 'patch' property with the diff
                if 'patch' in file:
                    file_changes[file['filename']] = file['patch']

            return {
                "title": pr_data.get('title'),
                "body": pr_data.get('body'),
                "url": pr_data.get('html_url'),
                "file_changes": file_changes
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub PR: {e}")
            return None

    def post_review_comment(self, owner: str, repo: str, pr_number: int, comment: str):
        """Posts a general review comment on a GitHub PR."""
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": comment}
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 201:
            print("Successfully posted general review comment on GitHub.")
        else:
            print(f"Failed to post general comment: {response.status_code} - {response.text}")

    def post_inline_comment(self, owner: str, repo: str, pr_number: int, file_path: str, line_number: int, comment: str):
        """Posts an inline comment on a specific line of a file in a GitHub PR."""
        # Note: Inline comments on GitHub require a diff_hunk, a position, and a comment body.
        # This is a simplified version for demonstration. A full implementation would need to parse the diff to find the correct position.
        print("Note: Inline commenting is not fully implemented. Posting as a general comment instead.")
        self.post_review_comment(owner, repo, pr_number, f"Review comment on file {file_path}, line {line_number}: {comment}")
        
# Placeholder for other Git clients
class GitlabClient(BaseGitClient):
    """Client for interacting with GitLab's API. (Placeholder)"""
    def fetch_pr_details(self, owner: str, repo: str, pr_number: int):
        print("GitLab client not implemented. Returning dummy data.")
        return {
            "title": "Dummy GitLab PR",
            "body": "This is a placeholder for a GitLab Merge Request.",
            "url": "https://gitlab.com/dummy/project/-/merge_requests/1",
            "file_changes": {"dummy.py": "def placeholder():\n    return 'This is a dummy change.'"}
        }

    def post_review_comment(self, owner: str, repo: str, pr_number: int, comment: str):
        print(f"GitLab client not implemented. Dummy comment: {comment}")

    def post_inline_comment(self, owner: str, repo: str, pr_number: int, file_path: str, line_number: int, comment: str):
        print(f"GitLab client not implemented. Dummy inline comment: {comment}")

class BitbucketClient(BaseGitClient):
    """Client for interacting with Bitbucket's API. (Placeholder)"""
    def fetch_pr_details(self, owner: str, repo: str, pr_number: int):
        print("Bitbucket client not implemented. Returning dummy data.")
        return {
            "title": "Dummy Bitbucket PR",
            "body": "This is a placeholder for a Bitbucket Pull Request.",
            "url": "https://bitbucket.org/dummy/project/pull-requests/1",
            "file_changes": {"dummy.js": "function dummy() {\n  console.log('Dummy change');\n}"}
        }

    def post_review_comment(self, owner: str, repo: str, pr_number: int, comment: str):
        print(f"Bitbucket client not implemented. Dummy comment: {comment}")

    def post_inline_comment(self, owner: str, repo: str, pr_number: int, file_path: str, line_number: int, comment: str):
        print(f"Bitbucket client not implemented. Dummy inline comment: {comment}")

def get_client(server_type: str, token: str):
    """Factory function to get the correct Git client."""
    if server_type.lower() == "github":
        return GitHubClient(token)
    elif server_type.lower() == "gitlab":
        return GitlabClient(token)
    elif server_type.lower() == "bitbucket":
        return BitbucketClient(token)
    else:
        raise ValueError(f"Unsupported Git server: {server_type}")
