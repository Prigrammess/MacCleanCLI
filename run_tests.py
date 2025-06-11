#!/usr/bin/env python3
"""
Simple test runner for macOS Cleaner
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run tests with proper Python path."""
    # Add current directory to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Run pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "-v", "--tb=short",
        "tests/"
    ])

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())