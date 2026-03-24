import anthropic
from dataclasses import dataclass
from .github_client import PRData


@dataclass
class PRAnalysis:
    suggested_title: str
    summary: str
    files_overview: str
    risks: list[str]
    breaking_changes: list[str]
    change_type: str  # feat / fix / refactor / chore / docs


SYSTEM_PROMPT = """You are an expert code reviewer and technical writer.
Analyze the given pull request diff and metadata, then respond ONLY with valid JSON.
No markdown, no explanation — just the JSON object."""

ANALYSIS_PROMPT = """Analyze this pull request and return a JSON object with exactly these fields:

{{
  "suggested_title": "A clear, conventional-commit style title (e.g. feat: add user auth endpoint)",
  "change_type": "One of: feat | fix | refactor | chore | docs | test | perf",
  "summary": "2-4 sentence plain-English summary of what this PR does and why",
  "files_overview": "A short paragraph grouping the changed files by concern (e.g. 'API layer changes in X, database schema updated in Y, tests added in Z')",
  "risks": ["list", "of", "potential", "risk", "items — empty array if none"],
  "breaking_changes": ["list", "of", "breaking", "changes — empty array if none"]
}}

--- PR METADATA ---
Title: {title}
Author: {author}
Branch: {head_branch} → {base_branch}
Files changed: {file_count}
Additions: +{additions} / Deletions: -{deletions}

Description provided by author:
{body}

--- FILES CHANGED ---
{files_list}

--- DIFF ---
{diff}
"""


class AIAnalyzer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def analyze(self, pr: PRData) -> PRAnalysis:
        """Send PR data to Claude and get structured analysis back."""
        files_list = self._format_files_list(pr.files_changed)

        prompt = ANALYSIS_PROMPT.format(
            title=pr.title,
            author=pr.author,
            head_branch=pr.head_branch,
            base_branch=pr.base_branch,
            file_count=len(pr.files_changed),
            additions=pr.additions,
            deletions=pr.deletions,
            body=pr.body or "No description provided.",
            files_list=files_list,
            diff=pr.diff,
        )

        message = self.client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        import json
        raw = message.content[0].text.strip()
        # Strip accidental markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())

        return PRAnalysis(
            suggested_title=data.get("suggested_title", pr.title),
            summary=data.get("summary", ""),
            files_overview=data.get("files_overview", ""),
            risks=data.get("risks", []),
            breaking_changes=data.get("breaking_changes", []),
            change_type=data.get("change_type", "chore"),
        )

    def _format_files_list(self, files: list[dict]) -> str:
        lines = []
        for f in files:
            status = f.get("status", "modified")
            additions = f.get("additions", 0)
            deletions = f.get("deletions", 0)
            filename = f.get("filename", "")
            lines.append(f"  [{status}] {filename} (+{additions}/-{deletions})")
        return "\n".join(lines)
