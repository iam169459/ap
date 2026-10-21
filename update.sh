#!/bin/bash
set -e
cd "$(dirname "$0")"
git fetch origin
git reset --hard origin/main
echo "Updated successfully."
