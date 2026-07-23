#!/usr/bin/env python3
"""Unified CLI for worldcup-predictor. Delegates to scripts/predict.mjs."""
import subprocess
import sys
import os

if __name__ == '__main__':
    script = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'predict.mjs')
    result = subprocess.run(['node', script] + sys.argv[1:])
    sys.exit(result.returncode)
