import os
import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class PRData:
    title: str
    body: str
    author: str
    base_branch: str
    head_branch: str
    diff: str
    files_changed: list[dict]
    additions: int
    deletions: int
    pr_number: int
    repo: str


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = "https://api.github.com"

    def get_pr_data(self, repo: str, pr_number: int) -> PRData:
        """Fetch all PR data needed for analysis."""
        pr = self._get_pr(repo, pr_number)
        diff = self._get_pr_diff(repo, pr_number)
        files = self._get_pr_files(repo, pr_number)

        return PRData(
            title=pr["title"],
            body=pr.get("body") or "",
            author=pr["user"]["login"],
            base_branch=pr["base"]["ref"],
            head_branch=pr["head"]["ref"],
            diff=diff,
            files_changed=files,
            additions=pr["additions"],
            deletions=pr["deletions"],
            pr_number=pr_number,
            repo=repo,
        )

    def post_comment(self, repo: str, pr_number: int, comment: str):
        """Post a comment on the PR."""
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        response = requests.post(url, headers=self.headers, json={"body": comment})
        response.raise_for_status()
        return response.json()

    def update_pr_title(self, repo: str, pr_number: int, new_title: str):
        """Update the PR title."""
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        response = requests.patch(url, headers=self.headers, json={"title": new_title})
        response.raise_for_status()

    def _get_pr(self, repo: str, pr_number: int) -> dict:
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _get_pr_diff(self, repo: str, pr_number: int) -> str:
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        # Truncate large diffs to avoid token limits
        diff = response.text
        max_chars = 80_000
        if len(diff) > max_chars:
            diff = diff[:max_chars] + "\n\n[... diff truncated due to size ...]"
        return diff

    def _get_pr_files(self, repo: str, pr_number: int) -> list[dict]:
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
