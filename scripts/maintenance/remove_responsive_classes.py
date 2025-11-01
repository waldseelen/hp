#!/usr/bin/env python3
"""
Script to remove responsive Tailwind CSS classes from HTML templates.
This script removes all mobile responsive breakpoint classes (sm:, md:, lg:, xl:, 2xl:)
and keeps only the largest/desktop versions.
"""

import glob
import os
import re
from typing import List, Tuple


def remove_responsive_classes(content: str) -> str:
    """Remove responsive Tailwind CSS classes from HTML content."""

    # Common patterns to replace
    replacements = [
        # Container responsive padding
        (r"px-4 sm:px-6 lg:px-8", "px-8"),
        (r"px-4 sm:px-6", "px-6"),
        # Text size responsiveness - keep largest
        (r"text-4xl md:text-6xl", "text-6xl"),
        (r"text-4xl md:text-5xl", "text-5xl"),
        (r"text-3xl md:text-4xl", "text-4xl"),
        (r"text-2xl md:text-3xl", "text-3xl"),
        (r"text-xl md:text-2xl", "text-2xl"),
        (r"text-lg md:text-xl", "text-xl"),
        (r"text-9xl md:text-\[12rem\]", "text-[12rem]"),
        (r"text-8xl md:text-9xl", "text-9xl"),
        # Grid responsiveness - keep largest layout
        (r"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3", "grid grid-cols-3"),
        (r"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4", "grid grid-cols-4"),
        (r"grid grid-cols-1 md:grid-cols-3", "grid grid-cols-3"),
        (r"grid grid-cols-1 md:grid-cols-2", "grid grid-cols-2"),
        (r"grid md:grid-cols-2 lg:grid-cols-3", "grid grid-cols-3"),
        (r"grid md:grid-cols-2", "grid grid-cols-2"),
        (r"grid md:grid-cols-3", "grid grid-cols-3"),
        (r"grid lg:grid-cols-2", "grid grid-cols-2"),
        (r"grid lg:grid-cols-3", "grid grid-cols-3"),
        (r"grid lg:grid-cols-4", "grid grid-cols-4"),
        # Flexbox responsiveness - keep desktop layout
        (r"flex flex-col sm:flex-row", "flex"),
        (r"flex flex-col md:flex-row", "flex"),
        (r"flex flex-col lg:flex-row", "flex"),
        # Spacing responsiveness - keep larger spacing
        (r"py-12 sm:py-20", "py-20"),
        (r"py-16 sm:py-24", "py-24"),
        (r"mb-8 sm:mb-12", "mb-12"),
        (r"mt-8 sm:mt-12", "mt-12"),
        # Size responsiveness - keep larger sizes
        (r"w-24 h-24 md:w-32 md:h-32", "w-32 h-32"),
        (r"w-16 h-16 md:w-20 md:h-20", "w-20 h-20"),
        (r"w-32 h-32 md:w-48 md:h-48", "w-48 h-48"),
        # Column spans
        (r"lg:col-span-2", "col-span-2"),
        (r"lg:col-span-3", "col-span-3"),
        (r"lg:col-span-1", "col-span-1"),
        (r"md:col-span-2", "col-span-2"),
        (r"md:col-span-3", "col-span-3"),
        # Space between items
        (r"space-y-4 sm:space-y-0 sm:space-x-4", "space-x-4"),
        (r"space-y-2 sm:space-y-0 sm:space-x-2", "space-x-2"),
        # Hidden/show responsive classes
        (r"hidden md:flex", "flex"),
        (r"hidden lg:flex", "flex"),
        (r"hidden sm:flex", "flex"),
        (r"md:hidden", "hidden"),
        (r"lg:hidden", "hidden"),
        (r"sm:hidden", "hidden"),
    ]

    # Apply all replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    # Generic removal of any remaining responsive classes
    # This removes any class that starts with sm:, md:, lg:, xl:, or 2xl:
    content = re.sub(r"\b(sm|md|lg|xl|2xl):[a-zA-Z0-9\[\]\/\-\.]*", "", content)

    # Clean up multiple spaces that might result from removals
    content = re.sub(r"\s+", " ", content)
    content = re.sub(r'class="\s+', 'class="', content)
    content = re.sub(r'\s+"', '"', content)
    content = re.sub(r'class=""', "", content)

    return content


def process_template_file(filepath: str) -> Tuple[bool, str]:
    """Process a single template file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            original_content = f.read()

        new_content = remove_responsive_classes(original_content)

        if original_content != new_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, f"Modified: {filepath}"
        else:
            return False, f"No changes needed: {filepath}"

    except Exception as e:
        return False, f"Error processing {filepath}: {str(e)}"


def main():
    """Main function to process all template files."""
    templates_dir = "D:/FILES/BEST/templates"

    if not os.path.exists(templates_dir):
        print(f"Templates directory not found: {templates_dir}")
        return

    # Find all HTML files recursively
    html_files = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))

    print(f"Found {len(html_files)} HTML template files")
    print("=" * 50)

    modified_files = []
    unchanged_files = []
    error_files = []

    for filepath in html_files:
        modified, message = process_template_file(filepath)
        print(message)

        if "Error" in message:
            error_files.append(filepath)
        elif modified:
            modified_files.append(filepath)
        else:
            unchanged_files.append(filepath)

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Total files processed: {len(html_files)}")
    print(f"Files modified: {len(modified_files)}")
    print(f"Files unchanged: {len(unchanged_files)}")
    print(f"Files with errors: {len(error_files)}")

    if modified_files:
        print(f"\nModified files:")
        for file in modified_files:
            rel_path = os.path.relpath(file, templates_dir)
            print(f"  - {rel_path}")

    if error_files:
        print(f"\nFiles with errors:")
        for file in error_files:
            rel_path = os.path.relpath(file, templates_dir)
            print(f"  - {rel_path}")


if __name__ == "__main__":
    main()
