#!/usr/bin/env python3
"""Unified CLI for worldcup-predictor. Delegates to scripts/predict.mjs."""
import subprocess
import sys
import os


def main() -> None:
    """Entry point."""
    script = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'predict.mjs')
    result = subprocess.run(['node', script] + sys.argv[1:])
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
