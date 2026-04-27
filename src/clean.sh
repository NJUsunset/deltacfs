#!/usr/bin/bash
# Remove all generated files.  Safe to invoke from any working directory.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo 'Cleaning generated files...'
rm -rf "$PROJECT_DIR/temp"
rm -rf "$PROJECT_DIR/logs"
rm -rf "$PROJECT_DIR/output"
echo 'Done.'
