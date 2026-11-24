"""Unit tests for configuration parsing and validation."""

from __future__ import annotations

import pytest

from keycast_overlay.config import OverlayConfig, parse_config


def test_parse_config_defaults(monkeypatch) -> None:
    for key in (
        "KEYCAST_MAX_KEYS",
        "KEYCAST_HIGHLIGHT",
        "KEYCAST_FONT_SIZE",
        "KEYCAST_MARGIN_TOP",
        "KEYCAST_MARGIN_RIGHT",
        "KEYCAST_CORNER",
        "KEYCAST_CLEAR_AFTER",
        "KEYCAST_OPACITY",
        "KEYCAST_DEMO",
    ):
        monkeypatch.delenv(key, raising=False)

    cfg = parse_config([])
    assert cfg == OverlayConfig()


def test_parse_config_cli_flags() -> None:
    cfg = parse_config([
        "--max-keys", "10",
        "--highlight", "4",
        "--font-size", "13",
        "--corner", "bottom-left",
        "--clear-after", "3.5",
        "--opacity", "0.85",
        "--demo",
    ])
    assert cfg.max_keys == 10
    assert cfg.highlight == 4
    assert cfg.font_size == 13
    assert cfg.corner == "bottom-left"
    assert cfg.clear_after == 3.5
    assert cfg.opacity == 0.85
    assert cfg.demo is True


def test_parse_config_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("KEYCAST_DEMO", "1")
    monkeypatch.setenv("KEYCAST_MAX_KEYS", "6")
    monkeypatch.setenv("KEYCAST_CORNER", "bottom-right")
    cfg = parse_config([])
    assert cfg.demo is True
    assert cfg.max_keys == 6
    assert cfg.corner == "bottom-right"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_keys": 0},
        {"highlight": -1},
        {"font_size": 4},
        {"corner": "center"},
        {"clear_after": -0.5},
        {"opacity": 0.1},
        {"opacity": 1.5},
    ],
)
def test_overlay_config_rejects_invalid_values(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        OverlayConfig(**kwargs)
