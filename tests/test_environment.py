"""Check for required linter executables."""

from utils import _is_linter_expected

from lintquarto.registry import Linters


def _is_linter_available(linters: Linters, name: str) -> bool:
    """Return True if the linter's executable is available on PATH."""
    try:
        linters.check_available(name)
    except FileNotFoundError:
        return False
    return True


def test_all_supported_linters_are_installed() -> None:
    """Fail if any supported linter executable is missing."""
    linters = Linters()

    missing = [
        name
        for name in linters.supported
        if _is_linter_expected(name)
        and not _is_linter_available(linters, name)
    ]

    assert not missing, (
        "Missing required linter executables: "
        f"{', '.join(sorted(missing))}. "
        "Install them or adjust the supported linter list."
    )
