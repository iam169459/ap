#!/bin/bash
set -e
cd "$(dirname "$0")"
git fetch origin
git reset --hard origin/main
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
echo "Updated and installed successfully."
