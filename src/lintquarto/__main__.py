"""Thin wrapper which just imports and calls the entry-point."""

from .main import main

if __name__ == "__main__":
    raise SystemExit(main())
