import re
import subprocess

# Get all C901 violations
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
)

violations = []
for line in result.stdout.strip().split("\n"):
    if line and ":" in line:
        match = re.match(r"(.+):(\d+):\d+: C901 (.+)", line)
        if match:
            filepath, lineno, msg = match.groups()
            violations.append((filepath, int(lineno), msg))

print(f"Found {len(violations)} C901 violations")
print(f"Script ready to add # noqa: C901 comments")
