#!/usr/bin/env python
"""Fix app_label in all Meta classes"""

import re

with open("apps/portfolio/models.py", "r", encoding="utf-8") as f:
    content = f.read()


# Pattern to find class Meta blocks and add app_label if missing
def add_app_label_to_meta(match):
    meta_block = match.group(0)

    # Check if app_label already exists
    if "app_label" in meta_block:
        return meta_block

    # Find the end of Meta class (next non-indented line or end of block)
    # Insert app_label before the dedent
    lines = meta_block.split("\n")
    result_lines = []

    for i, line in enumerate(lines):
        result_lines.append(line)
        # If this is the last indented line before a dedent or end
        if i < len(lines) - 1:
            next_line = lines[i + 1]
            # If next line is not indented or is empty, we need to add app_label
            if next_line and not next_line[0].isspace() and next_line.strip():
                result_lines.insert(-1, "        app_label = 'portfolio'")
                break

    return "\n".join(result_lines)


# Find all class definitions and check their Meta classes
pattern = r"class \w+\(models\.Model\):.*?(?=^class |\Z)"
matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))

print(f"Found {len(matches)} model classes")

# Process each match
for match in matches:
    class_content = match.group(0)
    class_match = re.search(r"class (\w+)", class_content)
    if not class_match:
        continue
    class_name = class_match.group(1)

    # Find Meta class in this class
    meta_match = re.search(
        r"    class Meta:.*?(?=\n    def |\n\nclass |\Z)", class_content, re.DOTALL
    )

    if meta_match:
        meta_content = meta_match.group(0)

        # Check if app_label exists
        if "app_label" not in meta_content:
            # Add app_label before the end of the Meta class
            lines = meta_content.split("\n")

            # Find last indented line
            last_indented_idx = -1
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() and lines[i][0].isspace():
                    last_indented_idx = i
                    break

            if last_indented_idx >= 0:
                # Insert app_label after last indented line
                lines.insert(last_indented_idx + 1, "        app_label = 'portfolio'")
                new_meta = "\n".join(lines)
                content = content.replace(meta_content, new_meta)
                print(f"Added app_label to {class_name}")

with open("apps/portfolio/models.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")
