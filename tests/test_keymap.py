"""Unit tests for Win32 VK code mapping and combo state tracking."""

from __future__ import annotations

from keycast_overlay.keymap import KeyStateTracker, vk_to_label

VK_LCONTROL = 0xA2
VK_LSHIFT = 0xA0
VK_LMENU = 0xA4
VK_LWIN = 0x5B
VK_RETURN = 0x0D
VK_BACK = 0x08
VK_SPACE = 0x20


def test_vk_to_label_letters_digits_and_special_keys() -> None:
    assert vk_to_label(ord("C")) == "C"
    assert vk_to_label(ord("7")) == "7"
    assert vk_to_label(VK_RETURN) == "Enter"
    assert vk_to_label(VK_BACK) == "⌫"
    assert vk_to_label(VK_SPACE) == "Space"
    assert vk_to_label(0x70) == "F1"
    assert vk_to_label(0x7B) == "F12"
    assert vk_to_label(0x26) == "↑"
    assert vk_to_label(0xBD) == "-"


def test_combo_emits_single_chip_in_canonical_modifier_order() -> None:
    tracker = KeyStateTracker(max_keys=8, highlight=3)
    assert tracker.handle_vk(VK_LSHIFT, True) is None
    assert tracker.handle_vk(VK_LCONTROL, True) is None
    assert tracker.handle_vk(ord("T"), True) == "Ctrl+Shift+T"
    # Releasing modifiers after a combo must NOT emit lone modifier chips
    assert tracker.handle_vk(ord("T"), False) is None
    assert tracker.handle_vk(VK_LCONTROL, False) is None
    assert tracker.handle_vk(VK_LSHIFT, False) is None
    assert tracker.keys == ["Ctrl+Shift+T"]


def test_lone_modifier_tap_emits_on_release_and_ignores_os_key_repeat() -> None:
    tracker = KeyStateTracker()
    assert tracker.handle_vk(VK_LWIN, True) is None
    # OS key repeat while holding Win
    assert tracker.handle_vk(VK_LWIN, True) is None
    assert tracker.handle_vk(VK_LWIN, False) == "Win"
    assert tracker.keys == ["Win"]


def test_rolling_window_and_gold_highlight_cutoff() -> None:
    tracker = KeyStateTracker(max_keys=4, highlight=2)
    for ch in ("A", "B", "C", "D", "E"):
        tracker.push(ch)

    assert tracker.keys == ["B", "C", "D", "E"]
    chips = tracker.chips()
    assert [(c.text, c.recent) for c in chips] == [
        ("B", False),
        ("C", False),
        ("D", True),
        ("E", True),
    ]


def test_clear_empties_keys_but_preserves_held_modifiers() -> None:
    tracker = KeyStateTracker()
    tracker.handle_vk(VK_LCONTROL, True)
    tracker.handle_vk(ord("C"), True)
    assert tracker.keys == ["Ctrl+C"]

    tracker.clear()
    assert tracker.keys == []
    assert tracker.handle_vk(ord("V"), True) == "Ctrl+V"
