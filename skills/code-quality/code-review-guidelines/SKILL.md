---
name: code-review-guidelines
description: When asynchronously reviewing peer code before merging into the main branch.
version: 1.0.0
tags: [code-quality, review, team]
---

# Code Review Guidelines

## When to use
- Evaluating a Pull Request / Merge Request.
- Providing constructive feedback to peers.
- Ensuring code quality and architectural standards are met.

## What it does
Provides a structured, objective, and empathetic framework for reviewing code to catch bugs, ensure maintainability, and share knowledge without causing friction.

## Workflow
1. **Understand the Goal**: Read the PR description and linked ticket to understand *why* the change exists before reading code.
2. **Review High-Level**: Check architecture, structural integrity, and logic. Does the design make sense? Are new dependencies justified?
3. **Review Low-Level**: Check for correct error handling, edge cases, off-by-one errors, and performance implications.
4. **Check Tests**: Ensure new logic is covered by unit/integration tests and that the tests test the actual behavior.
5. **Provide Feedback**: Leave comments that state the *why*. Differentiate between blocking requests and optional suggestions (e.g., using "Nit:").

## Rules
- Assume positive intent; critique the code, not the author.
- Automate style and formatting checks via Linters/Formatters (do not argue over spacing in a PR).
- Approve immediately if the code improves the codebase, even if it's not "perfect."

## Anti-patterns
- **Gatekeeping**: Blocking PRs over personal style preferences.
- **Rubber Stamping**: Approving large PRs without reading the code just to move tickets along.
- **Scope Creep**: Asking the author to fix unrelated legacy code near their changes.

## Output format
A completed PR review consisting of specific, actionable comments, a summary of architectural feedback, and an explicit Approval or Request for Changes.
