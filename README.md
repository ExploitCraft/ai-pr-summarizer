# 🤖 AI PR Summarizer

> Automatically summarize pull requests using Claude AI. Posts a rich comment with a summary, risk analysis, files overview, and a suggested conventional-commit title — every time a PR is opened.

![GitHub Action](https://img.shields.io/badge/GitHub%20Action-ready-2088FF?logo=github-actions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Powered%20by-Claude%20AI-D97757?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ What it does

Every time a PR is opened or updated, it automatically posts a comment like this:

---

### 🤖 AI PR Summary

**Type:** ✨ `feat`&nbsp;&nbsp;**Files:** `8`&nbsp;&nbsp;**Changes:** `+142 / -23`

### 💡 Suggested Title
```
feat: add JWT authentication to API endpoints
```

### 📋 Summary
This PR introduces JWT-based authentication across all API endpoints. It adds middleware for token validation, updates the user model to store refresh tokens, and includes comprehensive test coverage for auth flows.

### 📁 Files Overview
Authentication logic lives in `src/middleware/auth.py` and `src/models/user.py`. Route protection is applied in `src/api/routes.py`. Tests are added in `tests/test_auth.py`.

### 💥 Breaking Changes
- ⚠️ All API endpoints now require a `Authorization: Bearer <token>` header

### 🔍 Potential Risks
- Refresh token rotation logic may cause session invalidation on concurrent requests
- `SECRET_KEY` must be set in production environment or tokens will use an insecure default

---

## 🚀 Quick Start (GitHub Action)

**1. Add your Anthropic API key to repository secrets:**

Go to `Settings → Secrets → Actions → New repository secret`
- Name: `ANTHROPIC_API_KEY`
- Value: your key from [console.anthropic.com](https://console.anthropic.com)

**2. Create `.github/workflows/pr-summary.yml`:**

```yaml
name: AI PR Summary

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  summarize:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read

    steps:
      - name: AI PR Summarizer
        uses: your-username/ai-pr-summarizer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

That's it. Open a PR and the bot will comment automatically. ✅

---

## 💻 CLI Usage

```bash
# Install
pip install -r requirements.txt

# Set env vars
export GITHUB_TOKEN=ghp_...
export ANTHROPIC_API_KEY=sk-ant-...

# Print summary to terminal
python main.py --repo owner/repo --pr 42

# Post as a PR comment
python main.py --repo owner/repo --pr 42 --post-comment

# Also update the PR title
python main.py --repo owner/repo --pr 42 --post-comment --update-title

# Output raw markdown
python main.py --repo owner/repo --pr 42 --output markdown
```

---

## ⚙️ Action Inputs

| Input | Description | Default |
|---|---|---|
| `github_token` | GitHub token (auto-provided) | `${{ github.token }}` |
| `anthropic_api_key` | Your Anthropic API key | **required** |
| `post_comment` | Post summary as PR comment | `true` |
| `update_title` | Auto-update PR title with suggested title | `false` |

## 📤 Action Outputs

| Output | Description |
|---|---|
| `suggested_title` | Conventional-commit style title |
| `change_type` | `feat`, `fix`, `refactor`, `chore`, etc. |
| `summary` | Plain-English PR summary |
| `has_breaking_changes` | `true` or `false` |

Use outputs in downstream steps:

```yaml
- name: AI PR Summarizer
  id: summarizer
  uses: your-username/ai-pr-summarizer@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}

- name: Print summary
  run: echo "${{ steps.summarizer.outputs.summary }}"

- name: Block merge if breaking changes
  if: steps.summarizer.outputs.has_breaking_changes == 'true'
  run: |
    echo "⚠️ Breaking changes detected — please update CHANGELOG.md"
    exit 1
```

---

## 🏗️ Project Structure

```
ai-pr-summarizer/
├── action.yml                        # GitHub Action metadata
├── Dockerfile                        # Container for the Action
├── main.py                           # CLI + Action entrypoint
├── requirements.txt
├── pr_summarizer/
│   ├── github_client.py              # Fetches PR data via GitHub API
│   ├── ai_analyzer.py                # Sends diff to Claude, parses response
│   └── formatter.py                  # Renders Markdown comment & CLI output
└── .github/workflows/
    └── example-usage.yml             # Copy this into your own repo
```

---

## 🤝 Contributing

PRs welcome! Please open an issue first for major changes.

```bash
git clone https://github.com/your-username/ai-pr-summarizer
cd ai-pr-summarizer
pip install -r requirements.txt
python main.py --repo your-org/your-repo --pr 1
```

---

## 📄 License

MIT © your-username
