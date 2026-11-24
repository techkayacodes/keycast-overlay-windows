"""Win32 virtual-key mapping and combo state tracker."""

from __future__ import annotations

from dataclasses import dataclass

# Windows Virtual-Key (VK_*) constants for modifiers
VK_MODIFIERS: dict[int, str] = {
    0xA2: "Ctrl",   # VK_LCONTROL
    0xA3: "Ctrl",   # VK_RCONTROL
    0x11: "Ctrl",   # VK_CONTROL
    0xA0: "Shift",  # VK_LSHIFT
    0xA1: "Shift",  # VK_RSHIFT
    0x10: "Shift",  # VK_SHIFT
    0xA4: "Alt",    # VK_LMENU
    0xA5: "AltGr",  # VK_RMENU
    0x12: "Alt",    # VK_MENU
    0x5B: "Win",    # VK_LWIN
    0x5C: "Win",    # VK_RWIN
}

MOD_ORDER: tuple[str, ...] = ("Win", "Ctrl", "Alt", "AltGr", "Shift")

# Human-friendly key names matching keycast-overlay's compact chip labels
VK_NAMES: dict[int, str] = {
    0x08: "⌫",      # VK_BACK
    0x09: "Tab",    # VK_TAB
    0x0D: "Enter",  # VK_RETURN
    0x13: "Pause",  # VK_PAUSE
    0x14: "Caps",   # VK_CAPITAL
    0x1B: "Esc",    # VK_ESCAPE
    0x20: "Space",  # VK_SPACE
    0x21: "PgUp",   # VK_PRIOR
    0x22: "PgDn",   # VK_NEXT
    0x23: "End",    # VK_END
    0x24: "Home",   # VK_HOME
    0x25: "←",      # VK_LEFT
    0x26: "↑",      # VK_UP
    0x27: "→",      # VK_RIGHT
    0x28: "↓",      # VK_DOWN
    0x2C: "PrtSc",  # VK_SNAPSHOT
    0x2D: "Ins",    # VK_INSERT
    0x2E: "Del",    # VK_DELETE
    0x5D: "Menu",   # VK_APPS
    0x6A: "*",      # VK_MULTIPLY
    0x6B: "+",      # VK_ADD
    0x6D: "-",      # VK_SUBTRACT
    0x6E: ".",      # VK_DECIMAL
    0x6F: "/",      # VK_DIVIDE
    0x90: "Num",    # VK_NUMLOCK
    0x91: "ScrLk",  # VK_SCROLL
    0xBA: ";",      # VK_OEM_1
    0xBB: "=",      # VK_OEM_PLUS
    0xBC: ",",      # VK_OEM_COMMA
    0xBD: "-",      # VK_OEM_MINUS
    0xBE: ".",      # VK_OEM_PERIOD
    0xBF: "/",      # VK_OEM_2
    0xC0: "`",      # VK_OEM_3
    0xDB: "[",      # VK_OEM_4
    0xDC: "\\",     # VK_OEM_5
    0xDD: "]",      # VK_OEM_6
    0xDE: "'",      # VK_OEM_7
}

# Function keys F1-F24
for _i in range(1, 25):
    VK_NAMES[0x6F + _i] = f"F{_i}"

# Numpad digits 0-9
for _d in range(10):
    VK_NAMES[0x60 + _d] = str(_d)


def vk_to_label(vk_code: int) -> str | None:
    """Convert a Win32 virtual-key code into a display label."""
    if vk_code in VK_MODIFIERS:
        return VK_MODIFIERS[vk_code]
    if vk_code in VK_NAMES:
        return VK_NAMES[vk_code]
    # ASCII digits 0-9 (0x30-0x39) and uppercase letters A-Z (0x41-0x5A)
    if 0x30 <= vk_code <= 0x39 or 0x41 <= vk_code <= 0x5A:
        return chr(vk_code)
    return None


@dataclass(frozen=True)
class Chip:
    text: str
    recent: bool


class KeyStateTracker:
    """Tracks held modifiers and maintains the rolling list of recent key chips."""

    def __init__(self, max_keys: int = 8, highlight: int = 3) -> None:
        self.max_keys = max_keys
        self.highlight = highlight
        self.keys: list[str] = []
        self._held_vks: dict[int, str] = {}
        self._mod_used: bool = False

    @property
    def held_modifiers(self) -> list[str]:
        active = set(self._held_vks.values())
        return [m for m in MOD_ORDER if m in active]

    def handle_vk(self, vk_code: int, pressed: bool) -> str | None:
        """Process a key-down or key-up event.

        Returns the newly emitted chip text when a key or lone modifier tap
        should be added to the overlay, or None otherwise.
        """
        if vk_code in VK_MODIFIERS:
            label = VK_MODIFIERS[vk_code]
            if pressed:
                if not self._held_vks:
                    self._mod_used = False
                self._held_vks[vk_code] = label
            else:
                was_only_mod = (
                    not self._mod_used
                    and vk_code in self._held_vks
                    and set(self._held_vks.values()) == {label}
                )
                self._held_vks.pop(vk_code, None)
                if was_only_mod and not self._held_vks:
                    return self.push(label)
            return None

        if not pressed:
            return None

        label = vk_to_label(vk_code)
        if not label:
            return None

        mods = self.held_modifiers
        if mods:
            self._mod_used = True
            return self.push("+".join([*mods, label]))
        return self.push(label)

    def push(self, text: str) -> str:
        """Append a chip label directly (also used in demo mode)."""
        self.keys.append(text)
        if len(self.keys) > self.max_keys:
            del self.keys[:-self.max_keys]
        return text

    def clear(self) -> None:
        """Clear all displayed keys without dropping currently held modifiers."""
        self.keys.clear()

    def chips(self) -> list[Chip]:
        """Return chips in display order (oldest -> newest) with highlight flags."""
        total = len(self.keys)
        cutoff = total - self.highlight
        return [Chip(text=k, recent=(i >= cutoff)) for i, k in enumerate(self.keys)]
