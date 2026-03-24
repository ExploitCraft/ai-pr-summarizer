#!/usr/bin/env python3
"""
ai-pr-summarizer — CLI & GitHub Action entry point

Usage (CLI):
  python main.py --repo owner/repo --pr 42

Usage (GitHub Action):
  Reads from environment variables set by the Action runner.
"""

import os
import sys
import argparse

from pr_summarizer import (
    GitHubClient,
    AIAnalyzer,
    format_pr_comment,
    format_cli_output,
)


def get_args():
    parser = argparse.ArgumentParser(
        description="AI-powered PR summarizer using Claude"
    )
    parser.add_argument("--repo", help="Repository in owner/repo format")
    parser.add_argument("--pr", type=int, help="Pull request number")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        default=False,
        help="Post the summary as a PR comment (default: print to stdout)",
    )
    parser.add_argument(
        "--update-title",
        action="store_true",
        default=False,
        help="Update the PR title with the AI-suggested title",
    )
    parser.add_argument(
        "--output",
        choices=["cli", "markdown"],
        default="cli",
        help="Output format when printing to stdout",
    )
    return parser.parse_args()


def resolve_config(args):
    """Resolve config from CLI args or environment variables (for GitHub Actions)."""
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("INPUT_GITHUB_TOKEN")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("INPUT_ANTHROPIC_API_KEY")

    # GitHub Actions provides these automatically
    repo = args.repo or os.environ.get("INPUT_REPO") or os.environ.get("GITHUB_REPOSITORY")
    pr_number = args.pr or _get_pr_number_from_env()

    post_comment = args.post_comment or os.environ.get("INPUT_POST_COMMENT", "").lower() == "true"
    update_title = args.update_title or os.environ.get("INPUT_UPDATE_TITLE", "").lower() == "true"

    if not github_token:
        _die("❌ GITHUB_TOKEN is required (env var or --token flag)")
    if not anthropic_key:
        _die("❌ ANTHROPIC_API_KEY is required (env var)")
    if not repo:
        _die("❌ Repository is required (--repo or GITHUB_REPOSITORY env var)")
    if not pr_number:
        _die("❌ PR number is required (--pr or triggered from a pull_request event)")

    return {
        "github_token": github_token,
        "anthropic_key": anthropic_key,
        "repo": repo,
        "pr_number": pr_number,
        "post_comment": post_comment,
        "update_title": update_title,
    }


def _get_pr_number_from_env() -> int | None:
    """Extract PR number from GitHub Actions event context."""
    # Set via action.yml input
    val = os.environ.get("INPUT_PR_NUMBER")
    if val:
        return int(val)
    # Fallback: parse from GITHUB_REF (refs/pull/42/merge)
    ref = os.environ.get("GITHUB_REF", "")
    if "/pull/" in ref:
        try:
            return int(ref.split("/pull/")[1].split("/")[0])
        except (IndexError, ValueError):
            pass
    return None


def _die(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(1)


def main():
    args = get_args()
    config = resolve_config(args)

    print(f"🔍 Fetching PR #{config['pr_number']} from {config['repo']}...")
    github = GitHubClient(config["github_token"])
    pr_data = github.get_pr_data(config["repo"], config["pr_number"])

    print(f"🤖 Analyzing with Claude...")
    analyzer = AIAnalyzer(config["anthropic_key"])
    analysis = analyzer.analyze(pr_data)

    # Output
    if config["post_comment"]:
        comment = format_pr_comment(pr_data, analysis)
        print("💬 Posting comment to PR...")
        github.post_comment(config["repo"], config["pr_number"], comment)
        print("✅ Comment posted successfully!")
    else:
        if args.output == "markdown":
            print(format_pr_comment(pr_data, analysis))
        else:
            print(format_cli_output(pr_data, analysis))

    if config["update_title"]:
        print(f"✏️  Updating PR title to: {analysis.suggested_title}")
        github.update_pr_title(config["repo"], config["pr_number"], analysis.suggested_title)
        print("✅ Title updated!")

    # Set GitHub Actions output variables
    _set_action_output("suggested_title", analysis.suggested_title)
    _set_action_output("change_type", analysis.change_type)
    _set_action_output("summary", analysis.summary)
    _set_action_output("has_breaking_changes", str(bool(analysis.breaking_changes)).lower())


def _set_action_output(name: str, value: str):
    """Write to GitHub Actions output file if available."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            # Escape newlines for multiline values
            safe_value = value.replace("\n", "%0A")
            f.write(f"{name}={safe_value}\n")


if __name__ == "__main__":
    main()
