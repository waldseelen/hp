"""
Fix MD5 security warnings by adding usedforsecurity=False parameter
"""

import os
import re

# Files to fix based on Bandit report
files_to_fix = [
    "apps/core/utils/caching.py",
    "apps/main/cache_utils.py",
    "apps/portfolio/analytics.py",
    "apps/portfolio/cache.py",
    "apps/portfolio/cache_keys.py",
    "apps/portfolio/cache_utils.py",
    "apps/portfolio/middleware/cache_middleware.py",
    "apps/portfolio/middleware/static_optimization_middleware.py",
    "apps/portfolio/ratelimit.py",
    "apps/portfolio/templatetags/cache_tags.py",
]


def fix_md5_in_file(filepath):
    """Fix MD5 usage in a single file"""
    if not os.path.exists(filepath):
        print(f"⚠ File not found: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Pattern: hashlib.md5(...) but not hashlib.md5(..., usedforsecurity=False)
    # Replace with usedforsecurity=False
    pattern = r"hashlib\.md5\(([^)]+)\)"

    def replace_md5(match):
        arg = match.group(1)
        # Check if usedforsecurity already exists
        if "usedforsecurity" in arg:
            return match.group(0)  # Already fixed
        # Add usedforsecurity=False
        return f"hashlib.md5({arg}, usedforsecurity=False)"

    content = re.sub(pattern, replace_md5, content)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Fixed: {filepath}")
        return True
    else:
        print(f"○ No changes needed: {filepath}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("FIXING MD5 SECURITY WARNINGS")
    print("=" * 60)

    fixed_count = 0
    for filepath in files_to_fix:
        if fix_md5_in_file(filepath):
            fixed_count += 1

    print("\n" + "=" * 60)
    print(f"SUMMARY: Fixed {fixed_count}/{len(files_to_fix)} files")
    print("=" * 60)
