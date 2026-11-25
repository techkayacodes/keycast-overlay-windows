# keycast-overlay-windows

A lightweight, native **Windows 10 / 11** keystroke overlay that displays your most recent key presses in a translucent, click-through strip on screen.

Created by **Kemal Codes ([@techkayacodes](https://github.com/techkayacodes))** as the Windows edition of [keycast-overlay](https://github.com/techkayacodes/keycast-overlay), inspired by the Linux keystroke visualizer [Show Me The Key](https://github.com/AlynxZhou/showmethekey).

Built with **zero third-party runtime dependencies** (standard Python 3.10+, Tkinter, and native Win32 APIs via `ctypes`), designed for screen recordings, coding tutorials, live streams, and pair programming.

## Design & Signature Features

Designed by **[@techkayacodes](https://github.com/techkayacodes)** for maximum clarity without cluttering your workspace:

- **Gold recency highlight (`#d4af37`)**: the **3 most recent keystrokes** stand out with a crisp gold outline, subtle gold halo, and bold bright-white text so viewers instantly know what was just pressed.
- **Dimmed keystroke history**: older keystrokes automatically fade into a muted grey style (up to 8 keys visible at once), giving context for recent sequences without competing for attention.
- **Clean placement & compact sizing**: sized cleanly for readability and anchored by default in the upper-right below window title and browser tab bars (`margin-top: 84px`, `margin-right: 16px`), keeping window controls and tabs unobstructed.
- **Combo chips & lone modifier taps**: shortcuts appear as a single chip (`Ctrl+C`, `Win+Enter`, `Ctrl+Shift+T`), while standalone modifier taps (like `Win` or `Ctrl`) still display cleanly.
- **Fully click-through & focus-safe**: uses Win32 `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TOPMOST` so mouse clicks pass straight through, keyboard focus is never stolen, and the overlay stays out of Alt+Tab and the taskbar.
- **Instant privacy pause**: press `Ctrl+Alt+Shift+P` anytime to pause and hide the overlay before typing sensitive input; press it again to resume.
- **Single-instance safety**: uses a Windows named mutex (`Global\KeycastOverlayWindowsMutex`) so launching the app twice never duplicates keys.
- **Zero disk logging**: key labels live strictly in memory while displayed on screen and are never written to disk or transmitted anywhere.

## How It Works

Unlike the Wayland edition ([keycast-overlay](https://github.com/techkayacodes/keycast-overlay)), which reads input from `showmethekey-cli` and draws via GTK 4 + `gtk4-layer-shell`, this Windows edition is implemented natively for Windows:

1. **Global input capture**: registers a low-level Win32 keyboard hook (`SetWindowsHookExW` with `WH_KEYBOARD_LL`) on a dedicated background message-pump thread.
2. **Translucent click-through rendering**: draws anti-aliased rounded keycap chips on a chroma-key transparent, always-on-top Tkinter `Canvas` with Win32 extended styles applied to the top-level HWND.

## Installation

Requires **Windows 10 / 11** and **Python 3.10+** (no external Python packages required).

```powershell
git clone https://github.com/techkayacodes/keycast-overlay-windows.git
cd keycast-overlay-windows
.\install.ps1
```

To also launch automatically when you sign in to Windows:

```powershell
.\install.ps1 -Autostart
```

Or run directly from the repository without installing:

```powershell
python -m keycast_overlay
# Or double-click start-overlay.bat / keycast-overlay.pyw for a windowless launch
```

## Usage

```powershell
keycast-overlay                          # start live keystroke overlay
keycast-overlay --demo                   # preview static sample keys (no keyboard hook)
keycast-overlay --corner bottom-right    # anchor to bottom-right corner
keycast-overlay --margin-top 96          # adjust vertical placement (px)
keycast-overlay --clear-after 4          # auto-clear after 4s of inactivity
keycast-overlay --max-keys 10 --highlight 3 --font-size 12
```

### Configuration Options

All settings can be passed as CLI flags or set via environment variables:

| CLI Flag         | Environment Variable   | Default     | Description                                            |
|------------------|------------------------|-------------|--------------------------------------------------------|
| `--max-keys`     | `KEYCAST_MAX_KEYS`     | `8`         | Maximum number of key chips kept on screen             |
| `--highlight`    | `KEYCAST_HIGHLIGHT`    | `3`         | Number of newest keys highlighted in gold (`#d4af37`)  |
| `--font-size`    | `KEYCAST_FONT_SIZE`    | `11`        | Key label font size in points                          |
| `--corner`       | `KEYCAST_CORNER`       | `top-right` | `top-right`, `top-left`, `bottom-right`, `bottom-left` |
| `--margin-top`   | `KEYCAST_MARGIN_TOP`   | `84`        | Vertical margin from the screen edge (px)              |
| `--margin-right` | `KEYCAST_MARGIN_RIGHT` | `16`        | Horizontal margin from the screen edge (px)            |
| `--clear-after`  | `KEYCAST_CLEAR_AFTER`  | `0`         | Seconds idle before clearing keys (`0` = never clear)  |
| `--opacity`      | `KEYCAST_OPACITY`      | `0.90`      | Overlay opacity (`0.2` to `1.0`)                       |
| `--demo`         | `KEYCAST_DEMO`         | `0`         | Display static sample chips without starting the hook  |

## Running Tests

```powershell
pytest
```

## Privacy

Like any on-screen keystroke visualizer, this application listens to global keyboard events while active. It **only** renders keys on screen — it never writes keystrokes to disk and never sends data over the network. Press `Ctrl+Alt+Shift+P` to pause and hide the overlay before entering passwords during a recording or stream.

## Credits & Attribution

- **Original Inspiration — [Show Me The Key](https://github.com/AlynxZhou/showmethekey)** by [AlynxZhou](https://github.com/AlynxZhou): the original Linux keystroke visualizer that inspired the idea of a clean, real-time on-screen key display.
- **Windows Edition & Visual Design — [@techkayacodes](https://github.com/techkayacodes) (Kemal Codes)**: native Windows implementation, default screen placement and compact chip sizing, gold highlight (`#d4af37`) on the 3 most recent keystrokes, and dimmed greyed-out styling for older keys (shared with the Wayland edition, [keycast-overlay](https://github.com/techkayacodes/keycast-overlay)).

## License

MIT. See [LICENSE](LICENSE).
