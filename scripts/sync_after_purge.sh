#!/usr/bin/env bash
# Helper script to sync local clone after remote history rewrite
set -euo pipefail

echo "Ensure you have saved any local changes (commit or stash) before running this script."
git fetch origin
git checkout master
git reset --hard origin/master
echo "Synchronized to origin/master"
