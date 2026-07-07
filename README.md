# AI Security Code Review Agent

An event-driven security review agent built with [n8n](https://n8n.io) that automatically analyzes code changes for security vulnerabilities every time code is pushed to this repository.

## What it does

Every push to this repo triggers an automated pipeline that:
1. Fetches the full commit diff via the GitHub API
2. Sends the diff to an LLM (Groq, running LLaMA 3.1 8B) with a structured security-review prompt
3. Returns a severity rating, summary, and remediation recommendation — or an explicit "no issues" result if nothing concrete is found

## Architecture

```
GitHub push event
      │
      ▼
  n8n Webhook  ──────────────►  HTTP Request (GitHub API)
  (receives push payload)        fetches commit + file diff
                                        │
                                        ▼
                              Basic LLM Chain (Groq / LLaMA 3.1 8B)
                              reviews diff for security issues
                                        │
                                        ▼
                              Structured finding: severity,
                              summary, recommendation
```

**Components:**
- **Trigger** — GitHub repository webhook (`push` event) → n8n Webhook node
- **Enrichment** — HTTP Request node calling `GET /repos/{owner}/{repo}/commits/{sha}` via a fine-grained GitHub PAT (Contents: Read-only) to retrieve the file-level patch data
- **Reasoning** — Basic LLM Chain node using Groq's hosted inference API (`llama-3.1-8b-instant`) as the underlying chat model
- **Output** — structured text response, currently logged in n8n's execution history (Slack/GitHub-comment delivery planned)

## What the diff is checked for

- Hardcoded secrets, API keys, or credentials
- SQL injection via string concatenation
- Unsafe deserialization
- Command injection
- Unsanitized `eval()` / `exec()` / `os.system()` usage

## A design lesson: catching false positives

An early version of the prompt, when given a trivial documentation-only diff, still returned a fabricated finding ("hardcoded secret strings") despite there being no code or credentials in the change. This is a well-known failure mode for LLM-based security reranking — models can generate plausible-sounding risk assessments even when no real signal is present.

The prompt was redesigned into an explicit two-step process:
1. **Detection step** — check for concrete, checkable vulnerability patterns (real credential strings, string-concatenated SQL, unsafe `eval`/`exec`/`os.system`, unsafe deserialization)
2. **Reporting step** — only generate a severity/summary/recommendation if step 1 finds a genuine match; otherwise return a fixed "no security-relevant changes detected" response

This tightened version correctly escalated a deliberately vulnerable test commit (hardcoded API key + string-concatenated SQL query) to **Severity: Critical**, with an accurate recommendation to use parameterized queries.

## Setup

1. Create a GitHub webhook (`push` event) pointing at your n8n workflow's Production URL
2. Generate a fine-grained GitHub PAT with `Contents: Read-only` and `Metadata: Read-only` scoped to this repo
3. Add a Groq API key (free tier, no billing required) as a credential in n8n
4. Publish/activate the n8n workflow

## Stack

- [n8n](https://n8n.io) — workflow orchestration
- [GitHub REST API](https://docs.github.com/en/rest) — commit/diff retrieval
- [Groq](https://console.groq.com) — hosted LLM inference (LLaMA 3.1 8B)

## Status

Working end-to-end for single-commit pushes. Planned next steps: output delivery to Slack/GitHub PR comments, multi-file diff handling, and comparison against rule-based and ATT&CK-augmented reranking approaches explored in parallel SOC alert triage research.
