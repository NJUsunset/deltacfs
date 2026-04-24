#!/usr/bin/bash
# Convenience wrapper: runs main.py from the project root.
# The script must be invoked from the project root (or anywhere — main.py
# auto-detects its own project root via constant.py).

cd "$(dirname "$0")/.."
python3 main.py "$@"
