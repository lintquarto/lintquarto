"""Thin wrapper which just imports and calls the entry-point."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
