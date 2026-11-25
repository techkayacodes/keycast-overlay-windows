"""Native Win32 global keyboard hook, single-instance mutex, and click-through helpers."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import threading
from collections.abc import Callable

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008

GA_ROOT = 2
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040

ERROR_ALREADY_EXISTS = 183

ULONG_PTR = ctypes.c_size_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


LOW_LEVEL_KEYBOARD_PROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class SingleInstanceLock:
    """Windows named mutex ensuring only one live overlay instance runs."""

    def __init__(self, name: str = "Global\\KeycastOverlayWindowsMutex") -> None:
        self.name = name
        self._handle: int | None = None

    def acquire(self) -> bool:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        handle = kernel32.CreateMutexW(None, False, self.name)
        if not handle:
            return True
        last_err = ctypes.get_last_error()
        if last_err == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._handle = int(handle)
        return True

    def release(self) -> None:
        if self._handle:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle(wintypes.HANDLE(self._handle))
            self._handle = None


def resolve_top_level_hwnd(hwnd: int) -> int:
    """Resolve Tkinter's inner child HWND to its top-level Win32 frame HWND."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    root_hwnd = user32.GetAncestor(hwnd, GA_ROOT)
    return int(root_hwnd) if root_hwnd else int(hwnd)


def apply_clickthrough_styles(hwnd: int) -> int:
    """Mark a Win32 top-level window as click-through, non-activating, and topmost.

    Resolves Tkinter's inner HWND to its top-level parent so WS_EX_LAYERED is
    never applied to a child window (which would make it invisible on Windows).
    Returns the top-level HWND that was styled.
    """
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    top_hwnd = resolve_top_level_hwnd(hwnd)

    get_long = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
    set_long = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
    get_long.argtypes = [wintypes.HWND, ctypes.c_int]
    get_long.restype = ctypes.c_ssize_t
    set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    set_long.restype = ctypes.c_ssize_t

    ex_style = get_long(top_hwnd, GWL_EXSTYLE)
    new_style = (
        ex_style
        | WS_EX_LAYERED
        | WS_EX_TRANSPARENT
        | WS_EX_TOOLWINDOW
        | WS_EX_NOACTIVATE
    )
    if new_style != ex_style:
        set_long(top_hwnd, GWL_EXSTYLE, new_style)

    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos(
        top_hwnd,
        wintypes.HWND(HWND_TOPMOST),
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW,
    )
    return top_hwnd


class GlobalKeyboardListener:
    """Listens to global Windows keyboard events via SetWindowsHookExW(WH_KEYBOARD_LL)."""

    def __init__(self, on_event: Callable[[int, bool], None]) -> None:
        self._on_event = on_event
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._hook: int | None = None
        self._callback_ref = None
        self._ready = threading.Event()
        self._error: Exception | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="keycast-hook", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3.0)
        if self._error is not None:
            raise self._error

    def stop(self) -> None:
        if self._thread_id is not None:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _run(self) -> None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            LOW_LEVEL_KEYBOARD_PROC,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        ]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.CallNextHookEx.argtypes = [
            wintypes.HHOOK,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL

        self._thread_id = kernel32.GetCurrentThreadId()

        def _proc(n_code: int, w_param: int, l_param: int) -> int:
            if n_code >= 0 and l_param:
                info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    self._on_event(int(info.vkCode), True)
                elif w_param in (WM_KEYUP, WM_SYSKEYUP):
                    self._on_event(int(info.vkCode), False)
            return user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

        self._callback_ref = LOW_LEVEL_KEYBOARD_PROC(_proc)
        hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._callback_ref, None, 0)
        if not hook:
            err_code = ctypes.get_last_error()
            self._error = OSError(f"SetWindowsHookExW failed with error {err_code}")
            self._ready.set()
            return

        self._hook = hook
        self._ready.set()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
