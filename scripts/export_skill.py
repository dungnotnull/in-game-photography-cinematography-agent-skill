#!/usr/bin/env python
"""
export_skill.py - Skill Packaging and Distribution

This script packages the skill for distribution as a .skill file or
standard Python package.

Usage:
    python scripts/export_skill.py --format skill
    python scripts/export_skill.py --format wheel
    python scripts/export_skill.py --validate
"""

import argparse
import sys
import tarfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Set
import json
from datetime import datetime


# Files and directories to include in distribution
DISTRIBUTION_INCLUDE = {
    "CLAUDE.md",
    "PROJECT-detail.md",
    "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
    "README.md",
    "LICENSE",
    "SECOND-KNOWLEDGE-BRAIN.md",
    "requirements.txt",
    "pyproject.toml",
    "CHANGELOG.md",
    "skills/",
    "config/",
    "tools/",
    "references/",
    "assets/",
    "tests/",
}

# Files to exclude from distribution
DISTRIBUTION_EXCLUDE = {
    "__pycache__",
    "*.pyc",
    ".pyc",
    "*.pyo",
    ".git/",
    ".gitignore",
    "logs/",
    "*.log",
    ".DS_Store",
    "Thumbs.db",
    "tests/TEST_RESULTS.md",
    "progression.json",
    "DEVELOPMENT-TRACKING.md",
}


def should_include(file_path: Path, base_dir: Path) -> bool:
    """Determine if a file should be included in distribution."""
    rel_path = file_path.relative_to(base_dir)

    # Check exclusions
    for exclude in DISTRIBUTION_EXCLUDE:
        if exclude.endswith("/"):
            if exclude[:-1] in rel_path.parts:
                return False
        else:
            if file_path.name == exclude or file_path.suffix == exclude.replace("*", ""):
                return False

    # Check if in include set
    for include in DISTRIBUTION_INCLUDE:
        if include.endswith("/"):
            if rel_path.is_relative_to(include[:-1]):
                return True
        elif file_path.name == include or rel_path.match(include):
            return True

    return False


def create_skill_package(output_path: Path, project_root: Path) -> bool:
    """Create a .skill package for Claude Code distribution."""
    files_to_include = []

    for file_path in project_root.rglob("*"):
        if file_path.is_file() and should_include(file_path, project_root):
            files_to_include.append(file_path)

    # Create tar.gz archive
    with tarfile.open(output_path, "w:gz") as tar:
        for file_path in files_to_include:
            arcname = file_path.relative_to(project_root)
            tar.add(file_path, arcname=arcname)

    print(f"✓ Created .skill package: {output_path}")
    print(f"  Included {len(files_to_include)} files")

    return True


def create_wheel_package(output_path: Path, project_root: Path) -> bool:
    """Create a Python wheel package."""
    # Read pyproject.toml for metadata
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        print("Error: pyproject.toml not found")
        return False

    # Build using standard tools
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "build", "--wheel", str(project_root)],
            check=True,
            capture_output=True,
        )

        # Find the built wheel
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            wheels = list(dist_dir.glob("*.whl"))
            if wheels:
                shutil.copy(wheels[0], output_path)
                print(f"✓ Created wheel package: {output_path}")
                return True

        return False
    except subprocess.CalledProcessError as e:
        print(f"Error building wheel: {e}")
        return False
    except ImportError:
        print("Error: build module not installed. Install with: pip install build")
        return False


def validate_distribution(project_root: Path) -> bool:
    """Validate that all required files are present for distribution."""
    missing = []

    for required in DISTRIBUTION_INCLUDE:
        if required.endswith("/"):
            dir_path = project_root / required[:-1]
            if not dir_path.exists():
                missing.append(f"{required} (directory)")
        else:
            file_path = project_root / required
            if not file_path.exists():
                missing.append(f"{required} (file)")

    if missing:
        print("Missing required files for distribution:")
        for item in missing:
            print(f"  ✗ {item}")
        return False

    print("✓ All required files present for distribution")
    return True


def generate_manifest(project_root: Path) -> dict:
    """Generate a manifest of included files."""
    manifest = {
        "version": "2.0.0",
        "generated_at": datetime.now().isoformat(),
        "files": [],
    }

    for file_path in project_root.rglob("*"):
        if file_path.is_file() and should_include(file_path, project_root):
            rel_path = str(file_path.relative_to(project_root))
            manifest["files"].append({
                "path": rel_path,
                "size": file_path.stat().st_size,
                "checksum": file_path.name,  # Placeholder for actual checksum
            })

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Skill packaging and distribution")
    parser.add_argument("--format", choices=["skill", "wheel", "both"], default="skill",
                       help="Package format to generate")
    parser.add_argument("--output", type=Path, default=Path.cwd() / "dist",
                       help="Output directory for packages")
    parser.add_argument("--validate", action="store_true", help="Validate before packaging")
    parser.add_argument("--manifest", action="store_true", help="Generate manifest only")
    parser.add_argument("--name", default="in-game-photography-cinematography",
                       help="Base name for output files")

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    args.output.mkdir(parents=True, exist_ok=True)

    if args.validate:
        if not validate_distribution(project_root):
            sys.exit(1)

    if args.manifest:
        manifest = generate_manifest(project_root)
        manifest_file = args.output / f"{args.name}_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"✓ Generated manifest: {manifest_file}")

    # Generate packages
    success_count = 0

    if args.format in ["skill", "both"]:
        skill_output = args.output / f"{args.name}.skill"
        if create_skill_package(skill_output, project_root):
            success_count += 1

    if args.format in ["wheel", "both"]:
        wheel_output = args.output / f"{args.name}-2.0.0-py3-none-any.whl"
        if create_wheel_package(wheel_output, project_root):
            success_count += 1

    print(f"\n{'✓' if success_count == 2 or (args.format == 'skill' and success_count == 1) else '✗'} "
          f"Packaging complete: {success_count}/{2 if args.format == 'both' else 1} formats")


if __name__ == "__main__":
    main()
