#!/usr/bin/env bash
set -euo pipefail

# Run this from the Git repository root after copying the patch files in place.
# These commands remove generated/local files from Git tracking without deleting
# your local virtual environment or generated files from disk.
git rm -r --cached --ignore-unmatch venv .venv staticfiles
git rm -r --cached --ignore-unmatch ecom/__pycache__ ecomapp/__pycache__ basketapp/__pycache__ useraccounts/__pycache__
git rm --cached --ignore-unmatch db.sqlite3 stderr.log

git add .gitignore .vercelignore .python-version vercel.json requirements.txt ecom/settings.py ecomapp/utils.py VERCEL_DEPLOYMENT_FIX.md

echo
echo "Cleanup staged. Review with: git status"
echo "Then commit and push when satisfied."
