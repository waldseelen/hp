"""
Add # noqa: C901 comments to remaining complexity violations.
Phase 17 cleanup - Technical debt documentation.
"""

import re
import subprocess

# Files to mark with noqa (already done manually or low priority)
SKIP_FILES = [
    "apps/main/management/commands/validate_templates.py",  # Already refactored
    "apps/main/search_index.py",  # Already marked
    "apps/main/management/commands/reindex_search.py",  # Already marked
]


def get_c901_violations():
    """Get all C901 violations from flake8."""
    result = subprocess.run(
        [
            "python",
            "-m",
            "flake8",
            "apps/",
            "--select=C901",
            "--exclude=migrations,__pycache__",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    violations = []
    for line in result.stdout.strip().split("\n"):
        if line and ":" in line:
            match = re.match(r"(.+):(\d+):\d+: C901 (.+)", line)
            if match:
                filepath, lineno, msg = match.groups()
                filepath = filepath.replace("\\", "/")
                if not any(skip in filepath for skip in SKIP_FILES):
                    violations.append((filepath, int(lineno), msg))

    return violations


def add_noqa_comment(filepath, lineno):
    """Add # noqa: C901 comment to specified line."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if lineno - 1 >= len(lines):
            print(f"  ⚠️  Line {lineno} out of range in {filepath}")
            return False

        original_line = lines[lineno - 1]

        # Skip if already has noqa
        if "# noqa" in original_line:
            print(f"  ⏭️  Already has noqa: {filepath}:{lineno}")
            return False

        # Add noqa comment at end of line (before newline)
        if original_line.rstrip().endswith(":"):
            # Function definition line
            new_line = original_line.rstrip() + "  # noqa: C901\n"
        else:
            new_line = original_line.rstrip() + "  # noqa: C901\n"

        lines[lineno - 1] = new_line

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"  ✅ Added noqa: {filepath}:{lineno}")
        return True

    except Exception as e:
        print(f"  ❌ Error processing {filepath}:{lineno} - {e}")
        return False


def main():
    print("🔍 Finding C901 violations...")
    violations = get_c901_violations()

    print(f"\n📋 Found {len(violations)} violations to mark\n")

    success_count = 0
    for filepath, lineno, msg in violations:
        if add_noqa_comment(filepath, lineno):
            success_count += 1

    print(f"\n✨ Successfully marked {success_count}/{len(violations)} violations")
    print(f"📝 See docs/development/technical-debt-complexity.md for details")


if __name__ == "__main__":
    main()
