#!/usr/bin/env python
"""
seed_knowledge.py - Knowledge Base Seeding

This script seeds the SECOND-KNOWLEDGE-BRAIN.md with foundational
academic and professional references for the domain.

Usage:
    python scripts/seed_knowledge.py --domain photography
    python scripts/seed_knowledge.py --validate
"""

import argparse
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


# Domain knowledge seeds
DOMAIN_SEEDS = {
    "photography": [
        {
            "title": "The Photographer's Eye: Composition and Design for Better Digital Photos",
            "authors": "Michael Freeman",
            "year": 2007,
            "venue": "Focal Press",
            "identifier_type": "ISBN",
            "identifier": "978-0240809342",
            "tier": 2,
            "categories": ["composition", "photography"],
            "key_findings": "Comprehensive framework for photographic composition including depth, framing, light, and color.",
        },
        {
            "title": "The Elements of Color",
            "authors": "Johannes Itten",
            "year": 1970,
            "venue": "Van Nostrand Reinhold",
            "identifier_type": "ISBN",
            "identifier": "978-0471289278",
            "tier": 2,
            "categories": ["color", "theory"],
            "key_findings": "Color contrast and harmony principles that underpin mood association in visual media.",
        },
    ],
    "cinematography": [
        {
            "title": "Film Art: An Introduction",
            "authors": "David Bordwell, Kristin Thompson",
            "year": 2017,
            "venue": "McGraw-Hill",
            "identifier_type": "ISBN",
            "identifier": "978-1259544627",
            "tier": 2,
            "categories": ["cinematography", "film-theory"],
            "key_findings": "Fundamental principles of film form, narrative, and visual style including mise-en-scene and editing.",
        },
        {
            "title": "The Visual Story: Creating the Visual Structure of Film, TV and Digital Media",
            "authors": "Bruce Block",
            "year": 2008,
            "venue": "Focal Press",
            "identifier_type": "ISBN",
            "identifier": "978-0240807799",
            "tier": 2,
            "categories": ["visual-story", "composition"],
            "key_findings": "Visual structure components: space, line, shape, color, tone, movement, and rhythm.",
        },
        {
            "title": "Picture Composition for Film and Television",
            "authors": "Peter Ward",
            "year": 2003,
            "venue": "Focal Press",
            "identifier_type": "ISBN",
            "identifier": "978-0240516813",
            "tier": 2,
            "categories": ["composition", "film"],
            "key_findings": "Composition principles specific to moving images and screen direction.",
        },
    ],
    "virtual_photography": [
        {
            "title": "In-Game Photography: From Easter Egg to Cultural Practice",
            "authors": "Stuart Ullman, et al.",
            "year": 2020,
            "venue": "Game Studies",
            "identifier_type": "URL",
            "identifier": "https://gamestudies.org",
            "tier": 4,
            "categories": ["virtual-photography", "game-studies"],
            "key_findings": "Evolution of in-game photography from feature to cultural practice.",
        },
    ],
    "tools": [
        {
            "title": "NVIDIA Ansel — Developer Documentation",
            "authors": "NVIDIA Corporation",
            "year": 2023,
            "venue": "NVIDIA Developer",
            "identifier_type": "URL",
            "identifier": "https://developer.nvidia.com/ansel",
            "tier": 3,
            "categories": ["tools", "photo-mode"],
            "key_findings": "Technical specifications for Ansel photo mode integration.",
        },
        {
            "title": "AMD Radeon ReLive — User Guide",
            "authors": "AMD",
            "year": 2023,
            "venue": "AMD Support",
            "identifier_type": "URL",
            "identifier": "https://www.amd.com/en/support",
            "tier": 3,
            "categories": ["tools", "photo-mode"],
            "key_findings": "Photo mode capabilities and configuration for Radeon GPUs.",
        },
    ],
}


def format_knowledge_entry(entry: Dict[str, Any]) -> str:
    """Format a knowledge entry for SECOND-KNOWLEDGE-BRAIN.md."""
    lines = []
    lines.append(f"- **{entry['title']}**")
    lines.append(f"  - Authors: {entry['authors']}")
    lines.append(f"  - Year: {entry['year']}")
    lines.append(f"  - Venue: {entry['venue']}")
    lines.append(f"  - {entry['identifier_type']}: {entry['identifier']}")
    lines.append(f"  - Tier: {entry['tier']}")
    lines.append(f"  - Categories: {', '.join(entry['categories'])}")
    lines.append(f"  - Key findings: {entry['key_findings']}")
    return "\n  ".join(lines)


def seed_knowledge_base(domains: List[str]) -> int:
    """Seed the knowledge base with domain-specific entries."""
    knowledge_file = Path(__file__).parent.parent / "SECOND-KNOWLEDGE-BRAIN.md"

    if not knowledge_file.exists():
        print(f"Error: {knowledge_file} not found")
        return 0

    content = knowledge_file.read_text(encoding="utf-8")
    entries_added = 0

    # Find Section 7 (Knowledge Update Log)
    section_7_pattern = r"(## 7\. Knowledge Update Log)"
    match = re.search(section_7_pattern, content)

    if not match:
        print("Warning: Section 7 not found, appending to end")
        insert_position = len(content)
    else:
        insert_position = match.end()

    # Prepare new entries
    new_entries = []
    timestamp = datetime.now().strftime("%Y-%m-%d")

    for domain in domains:
        if domain not in DOMAIN_SEEDS:
            continue

        for entry in DOMAIN_SEEDS[domain]:
            # Check if already exists
            identifier_pattern = re.escape(entry['identifier'])
            if re.search(identifier_pattern, content):
                continue

            formatted_entry = f"\n### {timestamp} — {domain.upper()} Seed\n"
            formatted_entry += format_knowledge_entry(entry) + "\n"
            new_entries.append(formatted_entry)
            entries_added += 1

    # Insert new entries
    if new_entries:
        updated_content = content[:insert_position] + "".join(new_entries) + content[insert_position:]
        knowledge_file.write_text(updated_content, encoding="utf-8")
        print(f"Added {entries_added} knowledge entries for domains: {', '.join(domains)}")

    return entries_added


def validate_knowledge_base() -> bool:
    """Validate the knowledge base structure."""
    knowledge_file = Path(__file__).parent.parent / "SECOND-KNOWLEDGE-BRAIN.md"

    if not knowledge_file.exists():
        print(f"Error: {knowledge_file} not found")
        return False

    content = knowledge_file.read_text(encoding="utf-8")

    # Check for required sections
    required_sections = [
        "## 1. Core Concepts & Frameworks",
        "## 2. Key Research Papers & Standards",
        "## 3. State-of-the-Art Methods & Tools",
        "## 4. Authoritative Data Sources",
        "## 5. Analytical Frameworks",
        "## 6. Self-Update Protocol",
        "## 7. Knowledge Update Log",
    ]

    all_found = True
    for section in required_sections:
        if section not in content:
            print(f"Missing section: {section}")
            all_found = False

    return all_found


def main():
    parser = argparse.ArgumentParser(description="Knowledge base seeding and validation")
    parser.add_argument("--domain", nargs="+", choices=list(DOMAIN_SEEDS.keys()) + ["all"],
                       help="Domains to seed (photography, cinematography, virtual_photography, tools, or all)")
    parser.add_argument("--validate", action="store_true", help="Validate knowledge base structure")
    parser.add_argument("--list", action="store_true", help="List available domains and entries")

    args = parser.parse_args()

    if args.validate:
        print("Validating knowledge base structure...")
        if validate_knowledge_base():
            print("✓ Knowledge base structure is valid")
        else:
            print("✗ Knowledge base has structural issues")

    elif args.list:
        print("Available domains and entries:")
        for domain, entries in DOMAIN_SEEDS.items():
            print(f"\n{domain.upper()} ({len(entries)} entries):")
            for entry in entries:
                print(f"  - {entry['title']}")

    elif args.domain:
        domains = "all" if "all" in args.domain else args.domain
        if "all" in domains:
            domains = list(DOMAIN_SEEDS.keys())

        count = seed_knowledge_base(domains)
        if count == 0:
            print("No new entries added (may already exist)")

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
