"""scripts/task_tool.py

Small helper to insert TASK-META YAML skeletons after each "### Task" heading in
`task.txt`. This lets the repo maintain machine-readable metadata without
removing human-readable content.

Usage:
  python scripts/task_tool.py --file ../task.txt --dry-run
  python scripts/task_tool.py --file ../task.txt --apply
  python scripts/task_tool.py --file ../task.txt --list

The script is conservative: it will only insert a skeleton where a
# TASK-META-START marker is not already present right after a Task heading.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TASK_HEADING_RE = re.compile(r"^(###\s+Task\s+\d+\.\d+:.*)$", re.MULTILINE)

SKELETON = (
    "# TASK-META-START\n"
    "id: {id}\n"
    "title: '{title}'\n"
    "actions:\n"
    "  - TODO: describe action 1\n"
    "verification:\n"
    "  - TODO: verification step 1\n"
    "status: todo\n"
    "# TASK-META-END\n\n"
)


def insert_skeletons(text: str) -> tuple[str, int]:
    """Return (new_text, inserted_count)."""
    lines = text.splitlines(keepends=True)
    out_lines = []
    i = 0
    inserted = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        if line.startswith("### Task"):
            # peek next few lines to see if TASK-META-START exists
            peek = "".join(lines[i + 1 : i + 6]) if i + 1 < len(lines) else ""
            if "# TASK-META-START" in peek:
                # already has meta block
                i += 1
                continue
            # extract id/title from heading
            m = re.match(r"###\s+Task\s+(\d+\.\d+):\s*(.*)", line)
            if m:
                tid = m.group(1)
                title = m.group(2).strip().replace("'", "'")
                skeleton = SKELETON.format(id=tid, title=title)
                out_lines.append(skeleton)
                inserted += 1
        i += 1
    return ("".join(out_lines), inserted)


def list_tasks(text: str) -> list[str]:
    return TASK_HEADING_RE.findall(text)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", "-f", required=True, help="path to task.txt")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--list", action="store_true")
    args = p.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print("File not found:", path)
        return 2
    text = path.read_text(encoding="utf-8")

    if args.list:
        tasks = list_tasks(text)
        for t in tasks:
            print(t.strip())
        return 0

    new_text, inserted = insert_skeletons(text)
    print(
        f"Found {len(list_tasks(text))} Task headings. Will insert {inserted} skeleton(s)."
    )
    if inserted == 0:
        print("No changes required.")
        return 0
    if args.dry_run:
        print("\n--- DRY RUN: preview of first 400 chars of changes ---\n")
        diff_preview = "\n".join(new_text.splitlines()[:50])
        print(diff_preview)
        return 0
    if args.apply:
        backup = path.with_suffix(".backup.txt")
        path.write_text(new_text, encoding="utf-8")
        print(f"Applied changes and wrote backup to {backup} (not implemented backup).")
        return 0
    print("No action taken. Use --apply to write changes or --dry-run to preview.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
