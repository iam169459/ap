#!/bin/bash
set -e
cd "$(dirname "$0")"
git fetch origin
git reset --hard origin/main
pip install requests
echo "Updated and installed successfully."
