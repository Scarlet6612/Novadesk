import ctypes
from ctypes import wintypes
import os
import subprocess
import winreg

user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32

# Win32 Constants
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000

HWND_BOTTOM = 1
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

WM_COMMAND = 0x0111
CMD_TOGGLE_DESKTOP_ICONS = 0x7402  # 29698

# SHQueryUserNotificationState Constants
QUNS_NOT_PRESENT = 1
QUNS_BUSY = 2
QUNS_RUNNING_D3D_FULL_SCREEN = 3
QUNS_PRESENTATION_MODE = 4
QUNS_ACCEPTS_NOTIFICATIONS = 5
QUNS_QUIET_TIME = 6
QUNS_APP = 7

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

def switch_to_interactive_desktop():
    """Switches thread to Default interactive desktop if running in non-standard desktop."""
    try:
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

def get_wallpaper_workerw():
    """
    Finds or creates the WorkerW window used by Windows Shell for wallpaper rendering.
    Attaching our window to WorkerW makes it part of the desktop canvas, completely immune to Win+D.
    """
    switch_to_interactive_desktop()
    progman = user32.FindWindowW("Progman", None)
    if not progman:
        return 0

    # Request Explorer to spawn the WorkerW wallpaper window
    result = ctypes.c_ulong(0)
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, ctypes.byref(result))

    worker_w = [0]
    def enum_windows_callback(hwnd, lparam):
        shell_view = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
        if shell_view != 0:
            # The next WorkerW in the z-order hierarchy holds the wallpaper
            worker_w[0] = user32.FindWindowExW(0, hwnd, "WorkerW", None)
            return False
        return True

    user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
    return worker_w[0] if worker_w[0] != 0 else progman

def set_tool_window(hwnd):
    """
    Configures the window as a desktop tool window.
    Hides from Taskbar and Alt+Tab, and keeps it above the desktop wallpaper.
    """
    try:
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_TOOLWINDOW
        ex_style &= ~WS_EX_APPWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        user32.SetWindowPos(
            hwnd,
            HWND_NOTOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
        )
    except Exception as e:
        print(f"Error setting tool window: {e}")

def attach_to_desktop(hwnd):
    """
    Ensures the window stays cleanly on the desktop without being swallowed by wallpaper.
    """
    set_tool_window(hwnd)

def stick_to_bottom(hwnd):
    """Ensures window is not top-most without going behind the desktop canvas."""
    set_tool_window(hwnd)

def is_fullscreen_or_gaming() -> bool:
    """Detects whether an exclusive 3D game is active."""
    try:
        state = ctypes.c_int(0)
        hr = shell32.SHQueryUserNotificationState(ctypes.byref(state))
        if hr == 0:
            return state.value == QUNS_RUNNING_D3D_FULL_SCREEN
    except Exception:
        pass
    return False

def get_defview_handle():
    """Finds the SHELLDLL_DefView handle reliably."""
    switch_to_interactive_desktop()
    progman = user32.FindWindowW("Progman", None)
    found = [user32.FindWindowExW(progman, 0, "SHELLDLL_DefView", None)]

    if not found[0]:
        def enum_cb(hwnd, lparam):
            sv = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
            if sv:
                found[0] = sv
                return False
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    return found[0]

def is_desktop_icons_visible() -> bool:
    """Checks whether native desktop icons are visible in Windows registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 0, winreg.KEY_READ) as k:
            hide_val, _ = winreg.QueryValueEx(k, "HideIcons")
            return hide_val == 0
    except Exception:
        return True

def set_desktop_icons_visible(visible: bool):
    """Toggles native Windows desktop icons visibility."""
    try:
        current_visible = is_desktop_icons_visible()
        if current_visible != visible:
            sv = get_defview_handle()
            if sv:
                user32.SendMessageW(sv, WM_COMMAND, CMD_TOGGLE_DESKTOP_ICONS, 0)
    except Exception as e:
        print(f"Error toggling desktop icons: {e}")

def open_file(path: str):
    """Launches the file with Windows default handler."""
    try:
        os.startfile(path)
    except Exception as e:
        print(f"Error opening file {path}: {e}")

def show_in_explorer(path: str):
    """Reveals the file in Windows Explorer."""
    try:
        norm_path = os.path.normpath(path)
        subprocess.run(["explorer.exe", f"/select,{norm_path}"], check=False)
    except Exception as e:
        print(f"Error showing in explorer: {e}")
