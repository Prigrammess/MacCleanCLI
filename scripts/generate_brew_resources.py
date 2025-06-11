#!/usr/bin/env python3
"""
Generate Homebrew formula resources for Python dependencies
"""

import subprocess
import sys
import re
from pathlib import Path


def get_package_info(package_name):
    """Get package URL and SHA256 from PyPI."""
    try:
        # Get package info using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "-f", package_name],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return None

        # Parse version
        version_match = re.search(r"Version: (.+)", result.stdout)
        if not version_match:
            return None

        version = version_match.group(1)

        # Download and get hash
        download_result = subprocess.run(
            [sys.executable, "-m", "pip", "download", "--no-deps", f"{package_name}=={version}"],
            capture_output=True,
            text=True,
            cwd="/tmp"
        )

        if download_result.returncode != 0:
            return None

        # Find downloaded file
        import glob
        files = glob.glob(f"/tmp/{package_name}-{version}*")
        if not files:
            return None

        # Calculate SHA256
        import hashlib
        sha256 = hashlib.sha256()
        with open(files[0], 'rb') as f:
            sha256.update(f.read())

        # Clean up
        Path(files[0]).unlink()

        return {
            "name": package_name,
            "version": version,
            "url": f"https://files.pythonhosted.org/packages/{package_name}-{version}.tar.gz",
            "sha256": sha256.hexdigest()
        }

    except Exception as e:
        print(f"Error processing {package_name}: {e}")
        return None


def generate_formula_resources():
    """Generate Homebrew formula resources."""
    # Read requirements
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("requirements.txt not found!")
        return

    packages = []
    with open(requirements_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name
                package = re.split(r"[><=]", line)[0]
                packages.append(package)

    print("Generating Homebrew resources...")
    print()

    # Try using poet first
    try:
        poet_result = subprocess.run(
            ["poet", "macos-cleaner"],
            capture_output=True,
            text=True
        )

        if poet_result.returncode == 0:
            print(poet_result.stdout)
            return
    except FileNotFoundError:
        print("homebrew-pypi-poet not found, generating manually...")
        print("Install with: pip install homebrew-pypi-poet")
        print()

    # Manual generation
    for package in packages:
        if package in ["pytest", "pytest-cov", "black", "flake8", "mypy"]:
            continue  # Skip dev dependencies

        info = get_package_info(package)
        if info:
            print(f'  resource "{info["name"]}" do')
            print(f'    url "{info["url"]}"')
            print(f'    sha256 "{info["sha256"]}"')
            print('  end')
            print()


if __name__ == "__main__":
    generate_formula_resources()