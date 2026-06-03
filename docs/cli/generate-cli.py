"""Generate markdown formatted CLI documentation."""

import re
import subprocess
from pathlib import Path

# Output file where the generated CLI help documentation will be saved
TARGET = Path(__file__).parent / "cli-help.md"

# Run the CLI command and capture its help output
help_text = subprocess.run(
    ["lintquarto", "--help"],  # noqa: S607
    capture_output=True,
    text=True,
    check=True,
).stdout.rstrip()

# Split help output into lines for parsing
lines = help_text.splitlines()

# Storage for parsed sections
usage_lines = []
options = []
description_lines = []

in_usage = False
in_options = False
current_flag = None
current_desc = []

for line in lines:
    stripped = line.rstrip()

    # Start usage block
    if line.startswith("usage:"):
        in_usage = True
        usage_lines.append(line.removeprefix("usage:").strip())
        continue

    # Continue wrapped usage lines until a blank line or a new section
    if in_usage:
        if not line.strip():
            in_usage = False
            continue
        if line.strip() == "options:":
            in_usage = False
            in_options = True
            continue
        if line.startswith(" "):
            usage_lines.append(line.strip())
            continue
        else:
            in_usage = False

    # Capture description text between usage and options
    if not in_options and line.strip() and line.strip() != "options:":
        description_lines.append(line.strip())
        continue

    # Detect start of options section
    if line.strip() == "options:":
        in_options = True
        continue

    # Ignore anything outside options from here on
    if not in_options or not line.strip():
        continue

    # Detect a new option entry
    if re.match(r"^\s+-", stripped):
        if current_flag is not None:
            options.append((current_flag, " ".join(current_desc).strip()))

        match = re.match(r"^\s*(.+?)(?:\s{2,}(.+))?$", stripped)
        current_flag = match.group(1).strip()
        first_desc = match.group(2).strip() if match.group(2) else ""
        current_desc = [first_desc] if first_desc else []
    else:
        # Continuation line for a multi-line option description
        current_desc.append(stripped.strip())

# Save final option
if current_flag is not None:
    options.append((current_flag, " ".join(current_desc).strip()))

# Join wrapped usage back into one line
usage = " ".join(usage_lines)

# Format options as Markdown bullets
formatted_options = [
    f"* `{flag}` - {desc}" if desc else f"* `{flag}`" for flag, desc in options
]

# Build final Markdown output
output = "\n".join(
    [
        "Usage:",
        "",
        "```",
        usage,
        "```",
        "",
        *description_lines,
        "",
        "Options:",
        "",
        *formatted_options,
        "",
        "Passing extra arguments directly to linters is not supported.",
        "Only `.qmd` files are processed.",
    ]
)

# Write output to file
TARGET.write_text(output, encoding="utf-8")
