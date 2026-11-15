#!/usr/bin/env bash
# Turns on the tracked git hooks (commit labels, CODE-02) for this checkout.
set -euo pipefail
cd "$(dirname "$0")/.."
chmod +x githooks/prepare-commit-msg githooks/commit-msg
git config core.hooksPath githooks
echo "hooks on: $(git config core.hooksPath)"
