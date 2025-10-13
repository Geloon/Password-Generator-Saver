#!/usr/bin/env bash
set -euo pipefail

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "Please set GITHUB_TOKEN env var with repo scope."
  exit 1
fi

REPO="Geloon/Password-Generator-Saver"
HEAD_BRANCH="docs/notification"
BASE_BRANCH="master"
TITLE="$1"
BODY_FILE="ISSUE_TO_CREATE.md"

BODY=$(sed -n '1,200p' "$BODY_FILE" | sed '1,1d')

curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$REPO/pulls \
  -d "{\"title\": \"$TITLE\", \"head\": \"$HEAD_BRANCH\", \"base\": \"$BASE_BRANCH\", \"body\": \"$(printf "%s" "$BODY" | sed 's/"/\\"/g')\" }" | jq -r '.html_url'
