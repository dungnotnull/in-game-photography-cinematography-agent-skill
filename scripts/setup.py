#!/usr/bin/env python
"""
setup.py - Environment Setup and Validation

This script validates the environment, checks dependencies, and prepares
the skill for development or production use.

Usage:
    python scripts/setup.py --validate
    python scripts/setup.py --install-deps
    python scripts/setup.py --check
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
import json


# Required dependencies with version constraints
REQUIRED_DEPS = {
    "anthropic": ">=0.18.0",
    "requests": ">=2.31.0",
    "pydantic": ">=2.0.0",
    "tenacity": ">=8.2.0",
    "python-dateutil": ">=2.8.0",
}

OPTIONAL_DEPS = {
    "rich": ">=13.0.0",  # For pretty output
    "loguru": ">=0.7.0",  # For enhanced logging
}


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        return False, f"Python 3.10+ required, found {sys.version}"
    return True, f"Python {sys.version}"


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required dependencies are installed."""
    missing = []
    for package, version in REQUIRED_DEPS.items():
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(f"{package}>={version}")
    return len(missing) == 0, missing


def install_dependencies(missing: List[str]) -> bool:
    """Install missing dependencies."""
    print(f"Installing {len(missing)} missing packages...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing,
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")
        return False


def validate_project_structure() -> Tuple[bool, List[str]]:
    """Validate that required project files exist."""
    required_files = [
        "CLAUDE.md",
        "PROJECT-detail.md",
        "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
        "SECOND-KNOWLEDGE-BRAIN.md",
        "skills/main.md",
        "config/skill_registry.py",
        "config/agent_router.py",
        "config/hooks.py",
    ]

    missing = []
    project_root = Path(__file__).parent.parent

    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing.append(file_path)

    return len(missing) == 0, missing


def run_tests() -> bool:
    """Run project validation tests."""
    print("Running project tests...")
    project_root = Path(__file__).parent.parent

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Tests failed: {e}")
        return False
    except FileNotFoundError:
        print("pytest not installed. Install with: pip install pytest")
        return False


def main():
    parser = argparse.ArgumentParser(description="Skill environment setup and validation")
    parser.add_argument("--validate", action="store_true", help="Validate environment only")
    parser.add_argument("--install-deps", action="store_true", help="Install missing dependencies")
    parser.add_argument("--check", action="store_true", help="Run full project check")
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    args = parser.parse_args()

    print("=" * 60)
    print("In-Game Photography & Cinematography Skill - Setup")
    print("=" * 60)
    print()

    # Check Python version
    ok, msg = check_python_version()
    status = "✓" if ok else "✗"
    print(f"{status} Python version check: {msg}")
    if not ok:
        sys.exit(1)

    # Check dependencies
    deps_ok, missing = check_dependencies()
    status = "✓" if deps_ok else "✗"
    if deps_ok:
        print(f"{status} All dependencies installed")
    else:
        print(f"{status} Missing dependencies: {', '.join(missing)}")
        if args.install_deps:
            if install_dependencies(missing):
                print("✓ Dependencies installed successfully")
            else:
                sys.exit(1)

    # Validate project structure
    if args.check or args.validate:
        structure_ok, missing_files = validate_project_structure()
        status = "✓" if structure_ok else "✗"
        if structure_ok:
            print(f"{status} Project structure valid")
        else:
            print(f"{status} Missing files: {', '.join(missing_files)}")

    # Run tests
    if args.check:
        tests_ok = run_tests()
        status = "✓" if tests_ok else "✗"
        print(f"{status} Test suite: {'passed' if tests_ok else 'failed'}")

    print()
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
