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

BODY=$(sed '1,1d' "$BODY_FILE" | sed ':a;N;$!ba;s/"/\\"/g')

RESPONSE=$(curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$REPO/pulls \
  -d "{\"title\": \"$TITLE\", \"head\": \"$HEAD_BRANCH\", \"base\": \"$BASE_BRANCH\", \"body\": \"$BODY\" }")

# Try to extract html_url
URL=$(echo "$RESPONSE" | grep -o '"html_url": *"[^"]\+' | head -n1 | sed 's/"html_url": *"//')

if [ -n "$URL" ]; then
  echo "$URL"
else
  echo "Failed to create PR. Response:"
  echo "$RESPONSE"
  exit 1
fi
