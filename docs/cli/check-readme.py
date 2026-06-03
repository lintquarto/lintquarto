"""Check cli-help.md is consistent with README.md."""

import re
import sys
from pathlib import Path

readme = Path("README.md").read_text(encoding="utf-8")
cli_help = Path("docs/cli/cli-help.md").read_text(encoding="utf-8").strip()

match = re.search(
    r"<!-- cli-help:start -->\n(.*?)\n<!-- cli-help:end -->",
    readme,
    re.DOTALL,
)

if not match:
    print("Could not find README markers.")
    sys.exit(1)

readme_section = match.group(1).strip()

if readme_section != cli_help:
    print("README CLI help section is out of date.")
    sys.exit(1)

print("README CLI help section is up to date.")
