"""Configuration loading for keycast-overlay-windows."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

VALID_CORNERS = ("top-right", "top-left", "bottom-right", "bottom-left")


@dataclass(frozen=True)
class OverlayConfig:
    max_keys: int = 8
    highlight: int = 3
    font_size: int = 11
    margin_top: int = 12
    margin_right: int = 12
    corner: str = "top-right"
    clear_after: float = 0.0
    opacity: float = 0.90
    demo: bool = False

    def __post_init__(self) -> None:
        if self.max_keys < 1:
            raise ValueError("max_keys must be >= 1")
        if self.highlight < 0:
            raise ValueError("highlight must be >= 0")
        if self.font_size < 6:
            raise ValueError("font_size must be >= 6")
        if self.corner not in VALID_CORNERS:
            raise ValueError(f"corner must be one of {', '.join(VALID_CORNERS)}")
        if self.clear_after < 0:
            raise ValueError("clear_after must be >= 0")
        if not (0.2 <= self.opacity <= 1.0):
            raise ValueError("opacity must be between 0.2 and 1.0")


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw.strip())


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return float(raw.strip())


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keycast-overlay",
        description="Translucent, click-through Windows overlay showing recent keystrokes.",
    )
    parser.add_argument(
        "--max-keys",
        type=int,
        default=_env_int("KEYCAST_MAX_KEYS", 8),
        help="Maximum number of key chips shown on screen (default: 8).",
    )
    parser.add_argument(
        "--highlight",
        type=int,
        default=_env_int("KEYCAST_HIGHLIGHT", 3),
        help="Number of newest keys highlighted in gold (default: 3).",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=_env_int("KEYCAST_FONT_SIZE", 11),
        help="Key label font size in points (default: 11).",
    )
    parser.add_argument(
        "--margin-top",
        type=int,
        default=_env_int("KEYCAST_MARGIN_TOP", 12),
        help="Vertical margin from the screen edge in pixels (default: 12).",
    )
    parser.add_argument(
        "--margin-right",
        type=int,
        default=_env_int("KEYCAST_MARGIN_RIGHT", 12),
        help="Horizontal margin from the screen edge in pixels (default: 12).",
    )
    parser.add_argument(
        "--corner",
        choices=VALID_CORNERS,
        default=os.environ.get("KEYCAST_CORNER", "top-right"),
        help="Screen corner to anchor the overlay (default: top-right).",
    )
    parser.add_argument(
        "--clear-after",
        type=float,
        default=_env_float("KEYCAST_CLEAR_AFTER", 0.0),
        help="Seconds of idle time before clearing keys; 0 = never (default: 0).",
    )
    parser.add_argument(
        "--opacity",
        type=float,
        default=_env_float("KEYCAST_OPACITY", 0.90),
        help="Window opacity from 0.2 to 1.0 (default: 0.90).",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=_env_bool("KEYCAST_DEMO", False),
        help="Preview with sample keys without starting the keyboard hook.",
    )
    return parser


def parse_config(argv: list[str] | None = None) -> OverlayConfig:
    args = build_parser().parse_args(argv)
    return OverlayConfig(
        max_keys=args.max_keys,
        highlight=args.highlight,
        font_size=args.font_size,
        margin_top=args.margin_top,
        margin_right=args.margin_right,
        corner=args.corner,
        clear_after=args.clear_after,
        opacity=args.opacity,
        demo=args.demo,
    )
