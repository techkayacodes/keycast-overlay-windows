# keycast-overlay-windows

A lightweight, translucent, click-through keystroke overlay for **Windows 10 / 11** that displays your most recent key presses in a corner of the screen. The newest keys are highlighted with a gold outline (`#d4af37`) and bright white text while older keys fade into dimmer grey, so viewers can always tell what you just pressed.

Built as the native Windows companion to [keycast-overlay](https://github.com/techkayacodes/keycast-overlay) (Wayland), inspired by Linux's [Show Me The Key](https://github.com/AlynxZhou/showmethekey).

Great for screen recordings, tutorials, live streams, and pair programming — with **zero third-party runtime dependencies** (uses standard Python 3.10+, Tkinter, and native Win32 APIs via `ctypes`).

## Features

- **Last 8 keys on screen**, with the **3 newest highlighted in gold (`#d4af37`)** and bright white bold text.
- **Combos appear as one chip**: `Ctrl+C`, `Win+Enter`, `Ctrl+Shift+T`.
- **Lone modifier taps** (such as tapping `Win` or `Ctrl` by itself) still show up cleanly.
- **Truly click-through and non-intrusive**: uses Win32 `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TOPMOST` so it stays above all windows, never steals keyboard focus, never blocks mouse clicks, and stays out of Alt+Tab and the taskbar.
- **Instant privacy pause**: press `Ctrl+Alt+Shift+P` anytime to pause and hide the overlay (e.g., before typing passwords), and press it again to resume.
- **Single instance**: enforced via a Windows named mutex (`Global\KeycastOverlayWindowsMutex`) so launching it twice never duplicates keys.
- **Demo mode**: run with `--demo` or `KEYCAST_DEMO=1` to preview the overlay with sample keys without starting the keyboard hook.
- **Privacy first**: nothing is logged or written to disk. Key labels live only in memory while visible on screen.

## How It Works

On Linux/Wayland, [keycast-overlay](https://github.com/techkayacodes/keycast-overlay) reads global keyboard events through `showmethekey-cli` from [Show Me The Key](https://github.com/AlynxZhou/showmethekey) and renders via GTK 4 + `gtk4-layer-shell`.

On Windows, `keycast-overlay-windows` replaces those Linux-specific layers with native Win32 APIs:

1. **Global key capture**: installs a low-level keyboard hook (`SetWindowsHookExW` with `WH_KEYBOARD_LL`) on a background Win32 message-pump thread.
2. **Overlay window**: renders crisp rounded keycap chips on a chroma-key transparent, always-on-top Tkinter `Canvas` with click-through extended window styles.

## Install

Requires **Windows 10 / 11** and **Python 3.10+** (standard library only — no extra packages required).

```powershell
git clone https://github.com/techkayacodes/keycast-overlay-windows.git
cd keycast-overlay-windows
.\install.ps1
```

To also start automatically when you log in to Windows:

```powershell
.\install.ps1 -Autostart
```

Or run directly from the repo without installing:

```powershell
python -m keycast_overlay
# or double-click start-overlay.bat / keycast-overlay.pyw for windowless launch
```

## Usage

```powershell
keycast-overlay                          # start live overlay (top-right)
keycast-overlay --demo                   # preview with sample keys (no hook)
keycast-overlay --corner bottom-right    # anchor to bottom-right corner
keycast-overlay --clear-after 4          # auto-clear after 4s of inactivity
keycast-overlay --max-keys 10 --highlight 3 --font-size 12
```

### Configuration Options

Every option can be passed as a CLI flag or set as an environment variable:

| CLI Flag         | Env Var                | Default     | Meaning                                          |
|------------------|------------------------|-------------|--------------------------------------------------|
| `--max-keys`     | `KEYCAST_MAX_KEYS`     | `8`         | How many keys stay on screen                     |
| `--highlight`    | `KEYCAST_HIGHLIGHT`    | `3`         | How many newest keys get the gold outline        |
| `--font-size`    | `KEYCAST_FONT_SIZE`    | `11`        | Font size in points                              |
| `--corner`       | `KEYCAST_CORNER`       | `top-right` | `top-right`, `top-left`, `bottom-right`, `bottom-left` |
| `--margin-top`   | `KEYCAST_MARGIN_TOP`   | `12`        | Vertical margin from screen edge (px)            |
| `--margin-right` | `KEYCAST_MARGIN_RIGHT` | `12`        | Horizontal margin from screen edge (px)          |
| `--clear-after`  | `KEYCAST_CLEAR_AFTER`  | `0`         | Seconds idle before clearing (`0` = never)       |
| `--opacity`      | `KEYCAST_OPACITY`      | `0.90`      | Window opacity (`0.2` to `1.0`)                  |
| `--demo`         | `KEYCAST_DEMO`         | `0`         | Preview with sample keys without capturing input |

## Running Tests

```powershell
pytest
```

## Privacy

This program reads global keyboard events while active, just like any on-screen key visualizer. It **only** renders keys on screen — it never logs keystrokes to disk and never sends anything over the network. Use `Ctrl+Alt+Shift+P` to pause and hide the overlay before typing passwords on a recorded or shared screen.

## Credits & Acknowledgments

- **[Show Me The Key](https://github.com/AlynxZhou/showmethekey)** by [AlynxZhou](https://github.com/AlynxZhou) — original Linux keystroke visualizer whose design and `showmethekey-cli` powered the Wayland version and inspired this Windows port.
- **[keycast-overlay](https://github.com/techkayacodes/keycast-overlay)** by [Kemal Codes (@techkayacodes)](https://github.com/techkayacodes) — the original Wayland dark-and-gold translucent overlay that this Windows application is ported from.

## License

MIT. See [LICENSE](LICENSE).
