# Git Workflow — MLLM-Geo-AI Project

> **For all team members: Backend, Frontend, AI, and DevOps.**  
> Read this before writing a single line of code.

---

## Table of Contents

1. [Branch Strategy](#1-branch-strategy)
2. [Step-by-Step: How to Start a Task](#2-step-by-step-how-to-start-a-task) ← **new to the project? start here**
3. [Pull Request (PR) Process](#3-pull-request-pr-process)
4. [Code Review Rules](#4-code-review-rules)
5. [Branch Naming Convention](#5-branch-naming-convention)
6. [Commit Message Format](#6-commit-message-format)
7. [Git Cheat Sheet](#7-git-cheat-sheet)

---

## 1. Branch Strategy

We use **two permanent branches** only. Everything else is temporary.

```
fresh-start          ← stable base — the source of truth
    │
    ├── feature/load-area-endpoint
    ├── feature/mllm-builder-ui
    ├── fix/redis-connection-error
    └── chore/update-requirements
```

| Branch | Purpose | Who merges into it? |
|--------|---------|---------------------|
| `fresh-start` | Stable, reviewed code only | **Only the lead (after PR approval)** |
| `feature/*`, `fix/*`, `chore/*` | Your work-in-progress | You push here, then open a PR |

> ⚠️ **Never commit directly to `fresh-start`.** All changes go through a Pull Request.

---

## 2. Step-by-Step: How to Start a Task

---

### 🆕 First time on this project? Start here — Step 0

> If you have already cloned the repo before, skip to Step 1.

#### Step 0.1 — Install Git

If you don't have Git installed, download it first:

- **Windows**: https://git-scm.com/download/win → install with default options
- **macOS**: run `xcode-select --install` in Terminal, or https://git-scm.com/download/mac
- **Linux**: `sudo apt install git`

Verify it works:
```bash
git --version
# Expected output: git version 2.x.x
```

#### Step 0.2 — Set your identity (one time only)

Git needs to know who you are before you can commit anything:

```bash
git config --global user.name "Your Full Name"
git config --global user.email "your.email@example.com"
```

Confirm it was saved:
```bash
git config --global --list
# Should show: user.name=... and user.email=...
```

#### Step 0.3 — Clone the repository

Get the project URL from the lead (GitHub repository page → green "Code" button → copy the HTTPS URL), then run:

```bash
git clone https://github.com/<org>/MLLM_Geo_Ai.git
```

This creates a folder called `MLLM_Geo_Ai` on your machine with all the code inside.

#### Step 0.4 — Enter the project folder

```bash
cd MLLM_Geo_Ai
```

Every Git command from now on must be run from inside this folder.

#### Step 0.5 — Switch to the `fresh-start` branch

The default branch after cloning might be `main`. Switch to our base branch:

```bash
git checkout fresh-start
```

Confirm you're on the right branch:
```bash
git branch
# The branch with * next to it is the active one
# * fresh-start
```

You're all set. Continue to Step 1 below.

---

Follow these steps **every time** you start a new task.

### Step 1 — Make sure you have the latest `fresh-start`

```bash
git checkout fresh-start
git pull origin fresh-start
```

### Step 2 — Create your task branch

Branch off `fresh-start` with your task name (see [naming convention](#5-branch-naming-convention)):

```bash
git checkout -b feature/your-task-name
```

**Examples:**
```bash
git checkout -b feature/mllm-train-endpoint
git checkout -b feature/graph-topology-layer
git checkout -b fix/redis-not-connecting
git checkout -b chore/add-missing-tests
```

### Step 3 — Do your work and commit often

```bash
# Stage your changes
git add .

# Commit with a clear message (see format below)
git commit -m "feat: add POST /mllm/train endpoint with LoRA config"
```

Small, focused commits are better than one giant commit at the end.

### Step 4 — Push your branch to GitHub

```bash
git push origin feature/your-task-name
```

If it's your first push on this branch:
```bash
git push --set-upstream origin feature/your-task-name
```

### Step 5 — Open a Pull Request

Go to GitHub → your repository → click **"Compare & pull request"**.

- **Base branch:** `fresh-start`
- **Compare branch:** `feature/your-task-name`
- Write a clear PR description (what you did, why, how to test it)
- Assign a reviewer

### Step 6 — Wait for code review

Do **not** merge your own PR. The lead reviews it, requests changes if needed, and merges it into `fresh-start` when it's approved.

---

## 3. Pull Request (PR) Process

```
Developer                   Reviewer (Lead)
────────────────────────    ──────────────────────────
Opens PR                →   Reviews the code
                        ←   Requests changes (if any)
Makes fixes and pushes  →   Re-reviews
                        ←   ✅ Approves
                            Merges into fresh-start
                            Deletes the feature branch
```

### What to write in your PR description

```
## What does this PR do?
Adds the POST /api/v1/mllm/train endpoint with LoRA fine-tuning support.

## How to test it?
1. Start the server: python -m app.main
2. POST to /api/v1/mllm/train with the example body in the API docs
3. Poll /api/v1/mllm/status/{job_id} to see progress

## Related task / issue
Task #4 — MLLM Builder endpoints
```

---

## 4. Code Review Rules

### For the developer opening the PR

- Self-review your diff on GitHub before requesting a review — catch obvious mistakes yourself.
- Keep PRs small and focused. One task = one PR.
- Make sure the app still runs (`python -m app.main` should start without errors).
- Add or update tests when adding new functionality.

### For the reviewer (lead)

- Review within **24 hours** of the PR being opened.
- Check that the code matches the API contract in `api-contract-scalability-multi-modal-urban-ai.md`.
- Check that the code matches the PRD in `PRD_Urban_AI_Dashboard_v3.docx`.
- If changes are needed, leave clear comments on the specific lines.
- Only merge after the CI passes and you are satisfied with the code.

### After merge

The lead deletes the feature branch from GitHub after merging. The developer should also delete it locally:

```bash
git checkout fresh-start
git pull origin fresh-start
git branch -d feature/your-task-name
```

---

## 5. Branch Naming Convention

Format: `<type>/<short-description-in-kebab-case>`

| Type | When to use | Example |
|------|-------------|---------|
| `feature/` | New functionality from the PRD or upgrade plan | `feature/mllm-train-endpoint` |
| `fix/` | Bug fix or broken behavior | `fix/redis-connection-refused` |
| `chore/` | Maintenance: update deps, refactor, add tests | `chore/add-celery-worker-tests` |
| `docs/` | Documentation only | `docs/update-readme-setup` |

**Rules:**
- Lowercase only.
- Use hyphens `-`, not underscores or spaces.
- Be specific — `feature/endpoint` is bad, `feature/graph-topology-endpoint` is good.
- Keep it short (3–5 words maximum).

---

## 6. Commit Message Format

We follow a simplified version of [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>: <short description in present tense>
```

| Type | When to use |
|------|-------------|
| `feat` | New feature or endpoint |
| `fix` | Bug fix |
| `refactor` | Code change that doesn't add a feature or fix a bug |
| `test` | Adding or fixing tests |
| `docs` | Documentation only |
| `chore` | Build scripts, dependencies, config |

**Good examples:**
```
feat: add POST /api/v1/mllm/train endpoint
fix: handle Redis connection error gracefully on startup
test: add integration tests for classify endpoint
refactor: extract job tracking logic into JobStore class
docs: add GEE setup instructions to README
chore: update osmnx to 1.9.1
```

**Bad examples:**
```
done
update
fix stuff
WIP
changes
```

---

## 7. Git Cheat Sheet

### Setup (first time only)

```bash
# Set your name and email globally
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Clone the project
git clone <repository-url>
cd MLLM_Geo_Ai
```

---

### Daily Commands

```bash
# Check what branch you're on and what's changed
git status

# See recent commit history
git log --oneline -10

# See what changed in a file
git diff app/interfaces/api.py
```

---

### Branching

```bash
# List all local branches
git branch

# Create and switch to a new branch from fresh-start
git checkout fresh-start
git pull origin fresh-start
git checkout -b feature/my-task

# Switch between branches
git checkout fresh-start
git checkout feature/my-task

# Delete a local branch (after it's merged)
git branch -d feature/my-task
```

---

### Staging and Committing

```bash
# Stage all changed files
git add .

# Stage a specific file only
git add app/interfaces/api.py

# Commit staged changes
git commit -m "feat: add graph topology endpoint"

# Stage and commit in one step (only for tracked files)
git commit -am "fix: handle missing grid_id gracefully"

# Undo last commit (keeps changes in working directory)
git reset --soft HEAD~1
```

---

### Pushing and Pulling

```bash
# Push your branch to GitHub
git push origin feature/my-task

# First push (sets upstream automatically)
git push --set-upstream origin feature/my-task

# Pull latest changes from fresh-start
git checkout fresh-start
git pull origin fresh-start
```

---

### Syncing Your Branch with fresh-start

If `fresh-start` has been updated while you were working on your branch, sync it:

```bash
# While on your feature branch
git checkout feature/my-task

# Rebase onto the latest fresh-start
git fetch origin
git rebase origin/fresh-start
```

If there are conflicts, Git will pause and show you which files conflict. Open those files, resolve the conflicts (marked with `<<<<<<`), then:

```bash
git add .
git rebase --continue
```

---

### Handling Merge Conflicts

```bash
# See which files have conflicts
git status

# After fixing conflicts in your editor:
git add <conflicted-file>
git rebase --continue   # if rebasing
# OR
git commit              # if merging

# Abort and go back to before the conflict (escape hatch)
git rebase --abort
git merge --abort
```

---

### Stashing (Temporarily Save Unfinished Work)

```bash
# Save your unfinished changes temporarily
git stash

# Switch branches, do something, then come back and restore
git stash pop

# List all stashes
git stash list

# Discard the stash (if you don't need it)
git stash drop
```

---

### Undoing Mistakes

```bash
# Discard all uncommitted changes in a file
git checkout -- app/interfaces/api.py

# Discard ALL uncommitted changes (dangerous — can't undo)
git checkout -- .

# Undo last commit, keep changes staged
git reset --soft HEAD~1

# Undo last commit, keep changes unstaged
git reset HEAD~1

# See what a file looked like in a previous commit
git show abc1234:app/interfaces/api.py
```

---

### Useful Shortcuts

```bash
# Pretty graph of all branches
git log --oneline --graph --all --decorate

# Show who changed each line of a file
git blame app/interfaces/api.py

# Search for a string in all commits
git log -S "mllm_train" --oneline

# Show files changed in a commit
git show --stat abc1234
```

---

## Quick Reference Card

```
Start a task
────────────
git checkout fresh-start
git pull origin fresh-start
git checkout -b feature/your-task-name

During work
────────────
git add .
git commit -m "feat: what you did"

Push and open PR
────────────────
git push origin feature/your-task-name
→ Open PR on GitHub targeting fresh-start
→ Wait for review and approval
→ Lead merges

Clean up after merge
─────────────────────
git checkout fresh-start
git pull origin fresh-start
git branch -d feature/your-task-name
```

---

*MLLM-Geo-AI Project — Git Workflow v1.0*  
*Applies to: Urban AI Dashboard v3.0 development*