"""
setup_python.py — Environment setup helper (cross-platform).

Creates a Python virtual environment and installs required dependencies.

Usage (Windows):
    python scripts/setup_python.py

Usage (Linux/macOS):
    python scripts/setup_python.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
VENV_DIR = REPO_ROOT / ".venv"
ML_REQUIREMENTS = REPO_ROOT / "ml" / "requirements.txt"


def run(cmd: list, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    print("\n=== Voice Activator — Python Environment Setup ===\n")

    python = sys.executable

    # Create venv if it doesn't exist
    if not VENV_DIR.exists():
        print("Creating virtual environment...")
        run([python, "-m", "venv", str(VENV_DIR)])
    else:
        print(f"Virtualenv already exists at {VENV_DIR}")

    # Determine pip path
    if sys.platform == "win32":
        pip = str(VENV_DIR / "Scripts" / "pip")
    else:
        pip = str(VENV_DIR / "bin" / "pip")

    # Upgrade pip
    print("\nUpgrading pip...")
    run([pip, "install", "--upgrade", "pip", "--quiet"])

    # Install ML requirements
    print("\nInstalling ml/requirements.txt...")
    run([pip, "install", "-r", str(ML_REQUIREMENTS), "--quiet"])

    # Install pytest
    print("\nInstalling pytest...")
    run([pip, "install", "pytest", "--quiet"])

    print("\n=== Setup complete ===")
    print("Activate the environment:")
    if sys.platform == "win32":
        print(f"  .venv\\Scripts\\activate")
    else:
        print(f"  source .venv/bin/activate")
    print("Run tests:")
    print("  pytest tests/ -v\n")


if __name__ == "__main__":
    main()
