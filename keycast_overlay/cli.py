"""Command-line entry point for keycast-overlay-windows."""

from __future__ import annotations

import sys

from .config import parse_config
from .overlay import KeycastOverlayApp


def main(argv: list[str] | None = None) -> int:
    try:
        config = parse_config(argv)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    app = KeycastOverlayApp(config)
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
