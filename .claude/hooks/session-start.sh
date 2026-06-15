#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "Installing agentic-erp-patterns dev dependencies..."
pip install -e ".[dev]" --quiet

# Set test placeholder so unit tests run without a real key
echo 'export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-sk-test-placeholder}"' >> "$CLAUDE_ENV_FILE"

echo "Setup complete."
