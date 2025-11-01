import re
from pathlib import Path

pattern = re.compile(r".*[çğıöşüÇĞİÖŞÜ].*")
results = {}
for path in Path(".").rglob("*"):
    if not path.is_file():
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    matches = [line.strip() for line in text.splitlines() if pattern.search(line)]
    if matches:
        results[path.as_posix()] = matches

for file in sorted(results):
    print(f"== {file}")
    seen = set()
    for line in results[file]:
        if line in seen:
            continue
        seen.add(line)
        print(line)
    print()
