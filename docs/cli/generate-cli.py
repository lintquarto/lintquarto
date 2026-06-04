"""Generate markdown formatted CLI documentation."""

from __future__ import annotations

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
commands = []
description_lines = []

in_usage = False
in_options = False
in_commands = False
current_flag = None
current_desc = []


def flush_current(
    flag: str | None,
    desc: list[str],
    target_list: list[tuple[str, str]],
) -> None:
    """Append the current flag and accumulated description if a flag exists."""
    if flag is not None:
        target_list.append((flag, " ".join(desc).strip()))


for line in lines:
    stripped = line.rstrip()

    # Start usage block
    if line.startswith("usage:"):
        in_usage = True
        usage_lines.append(line.removeprefix("usage:").strip())
        continue

    # Continue wrapped usage lines
    if in_usage:
        if not line.strip():
            in_usage = False
            continue
        if line.strip() in ("options:", "commands:"):
            in_usage = False
            in_options = line.strip() == "options:"
            in_commands = line.strip() == "commands:"
            continue
        if line.startswith(" "):
            usage_lines.append(line.strip())
            continue
        else:
            in_usage = False

    # Capture description between usage and options/commands
    if (
        not in_options
        and not in_commands
        and line.strip()
        and line.strip() not in ("options:", "commands:")
    ):
        description_lines.append(line.strip())
        continue

    # Detect section headers
    if line.strip() == "options:":
        flush_current(
            current_flag, current_desc, commands if in_commands else options
        )
        current_flag, current_desc = None, []
        in_options = True
        in_commands = False
        continue

    if line.strip() in ("commands:", "positional arguments:"):
        flush_current(current_flag, current_desc, options)
        current_flag, current_desc = None, []
        in_commands = True
        in_options = False
        continue

    if not (in_options or in_commands) or not line.strip():
        continue

    # Skip argparse subparser group header lines like "{list} ..."
    if re.match(r"^\s*\{[^}]+\}", stripped):
        continue

    # Detect a new entry: option (starts with a dash) or command (any word)
    is_new_option = in_options and re.match(r"^\s+-", stripped)
    is_new_command = in_commands and re.match(r"^\s+\w", stripped)

    if is_new_option or is_new_command:
        target = options if in_options else commands
        flush_current(current_flag, current_desc, target)

        match = re.match(r"^\s*(.+?)(?:\s{2,}(.+))?$", stripped)
        current_flag = match.group(1).strip()
        first_desc = match.group(2).strip() if match.group(2) else ""
        current_desc = [first_desc] if first_desc else []
    else:
        # Continuation line — append to current description
        current_desc.append(stripped.strip())

# Flush final entry
target = commands if in_commands else options
flush_current(current_flag, current_desc, target)

usage = " ".join(usage_lines)

formatted_options = [
    f"* `{flag}` - {desc}" if desc else f"* `{flag}`" for flag, desc in options
]

formatted_commands = [
    f"* `{flag}` - {desc}" if desc else f"* `{flag}`"
    for flag, desc in commands
]

sections = [
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
]

if formatted_commands:
    sections += [
        "",
        "Commands:",
        "",
        *formatted_commands,
    ]

sections += [
    "",
    "Passing extra arguments directly to linters is not supported.",
    "Only `.qmd` files are processed.",
]

output = "\n".join(sections)

TARGET.write_text(output, encoding="utf-8")
