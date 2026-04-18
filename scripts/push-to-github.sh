#!/usr/bin/env bash
# Meridian Airport PMO suite — one-shot bootstrap to GitHub.
# (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
# Proprietary — unauthorised copying, distribution, modification or use prohibited.
#
# Runs ONCE on your laptop the first time you push this repo to GitHub.
# Creates a new private repo under the account `gh` is authenticated as,
# commits everything in the working tree, and pushes to main.
#
# Prereqs:
#   - git installed (macOS: `brew install git`).
#   - gh CLI installed (macOS: `brew install gh`) and authenticated:
#       gh auth login      # choose GitHub.com → HTTPS → Login with a browser
#     (Verify with:  gh auth status)
#   - You run this from the `meridian/` directory.
#
# After this script finishes:
#   1. Note the repo URL it prints.
#   2. Sign in to https://dashboard.render.com.
#   3. Blueprints → New Blueprint Instance → connect the GitHub account
#      → select this repo → Apply. See DEPLOY.md §11 for the full runbook.
#
# Usage:
#   ./scripts/push-to-github.sh                      # default repo name `meridian`
#   REPO_NAME=meridian-pilot ./scripts/push-to-github.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

REPO_NAME="${REPO_NAME:-meridian}"
VISIBILITY="${VISIBILITY:-private}"     # private | public
INITIAL_COMMIT_MSG="Meridian Airport PMO suite — pilot-demo bring-up"

echo "==> Meridian → GitHub bootstrap"
echo "    working dir: $ROOT_DIR"
echo "    repo name:   $REPO_NAME"
echo "    visibility:  $VISIBILITY"

# --- 1. prereq checks ----------------------------------------------------
command -v git >/dev/null 2>&1 || { echo "ERROR: git not on PATH" >&2; exit 1; }
command -v gh  >/dev/null 2>&1 || { echo "ERROR: gh CLI not on PATH. Install from https://cli.github.com/ and run 'gh auth login' first." >&2; exit 1; }

if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

GH_USER="$(gh api user --jq .login 2>/dev/null || true)"
if [[ -z "$GH_USER" ]]; then
  echo "ERROR: could not resolve your GitHub username from 'gh api user'." >&2
  exit 1
fi
echo "    authenticated as: $GH_USER"

# --- 2. git init (idempotent) --------------------------------------------
if [[ ! -d .git ]]; then
  echo "==> git init -b main"
  git init -b main >/dev/null
else
  echo "==> .git already exists — reusing"
fi

git config user.email "gaurav1976@gmail.com"
git config user.name  "Gaurav Vatsa"

# --- 3. stage + commit ---------------------------------------------------
git add -A
if git diff --cached --quiet; then
  echo "==> nothing to commit — tree already clean at HEAD"
else
  echo "==> git commit"
  git commit -m "$INITIAL_COMMIT_MSG" >/dev/null
fi

# --- 4. create the remote ------------------------------------------------
REMOTE_URL="https://github.com/${GH_USER}/${REPO_NAME}.git"

if gh repo view "${GH_USER}/${REPO_NAME}" >/dev/null 2>&1; then
  echo "==> GitHub repo ${GH_USER}/${REPO_NAME} already exists — skipping create"
else
  echo "==> gh repo create ${GH_USER}/${REPO_NAME} (${VISIBILITY})"
  gh repo create "${GH_USER}/${REPO_NAME}" --"${VISIBILITY}" --source=. --remote=origin --push
  echo
  echo "==> Done. Repo created and first commit pushed."
  echo "    $REMOTE_URL"
  exit 0
fi

# --- 5. push (if repo existed already) -----------------------------------
if git remote get-url origin >/dev/null 2>&1; then
  echo "==> origin remote already configured"
else
  git remote add origin "$REMOTE_URL"
fi

echo "==> git push -u origin main"
git push -u origin main

echo
echo "==> Done."
echo "    $REMOTE_URL"
