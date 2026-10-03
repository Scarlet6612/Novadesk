import sys
import os
import winreg
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen

from box_window import BoxWindow
from config import load_config, save_config
import win32_helper

APP_NAME = "NovaDesk"
REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

def create_app_icon():
    """Generates a modern rounded desktop icon with gradient/color."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded rectangle background
    brush = QBrush(QColor(59, 130, 246))  # Modern Blue
    painter.setBrush(brush)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 16, 16)

    # Accent inner border
    pen = QPen(QColor(255, 255, 255, 120), 2)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(8, 8, 48, 48, 12, 12)

    # Desktop fence icon representation (4 small squares)
    painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(16, 16, 13, 13, 3, 3)
    painter.drawRoundedRect(35, 16, 13, 13, 3, 3)
    painter.drawRoundedRect(16, 35, 13, 13, 3, 3)
    painter.drawRoundedRect(35, 35, 13, 13, 3, 3)

    painter.end()
    return QIcon(pix)

def is_auto_start_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False

def set_auto_start(enabled: bool):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                if getattr(sys, 'frozen', False):
                    exe_path = f'"{sys.executable}"'
                else:
                    exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
    except Exception as e:
        print(f"Error setting auto-start: {e}")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    icon = create_app_icon()
    app.setWindowIcon(icon)

    # Ensure Auto-Start is configured on Windows
    if not is_auto_start_enabled():
        set_auto_start(True)

    window = BoxWindow()
    window.show()

    # System Tray
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip(f"{APP_NAME} - Applications")

    tray_menu = QMenu()
    
    act_expand = tray_menu.addAction("Kutuyu Göster (Genişlet)")
    act_expand.triggered.connect(window.expand_to_full)

    act_collapse = tray_menu.addAction("Sol Üstte 'Applications' Yap")
    act_collapse.triggered.connect(window.collapse_to_pill)

    act_snap = tray_menu.addAction("Sol Üste Hizala")
    act_snap.triggered.connect(window.snap_to_top_left)

    act_refresh = tray_menu.addAction("Masaüstünü Yenile")
    act_refresh.triggered.connect(window.refresh_items)

    tray_menu.addSeparator()

    act_lock = tray_menu.addAction("Konumu Kilitle")
    act_lock.setCheckable(True)
    act_lock.setChecked(window.is_locked)
    act_lock.triggered.connect(window.toggle_lock)

    act_hide_desktop = tray_menu.addAction("Masaüstü Simgelerini Gizle")
    act_hide_desktop.setCheckable(True)
    act_hide_desktop.setChecked(window.hide_desktop_icons)
    act_hide_desktop.triggered.connect(window.toggle_desktop_icons)

    act_autostart = tray_menu.addAction("Windows ile Otomatik Başlat")
    act_autostart.setCheckable(True)
    act_autostart.setChecked(is_auto_start_enabled())
    act_autostart.triggered.connect(lambda ch: set_auto_start(ch))

    tray_menu.addSeparator()

    def on_quit():
        # Restore native desktop icons before exit
        win32_helper.set_desktop_icons_visible(True)
        app.quit()

    act_quit = tray_menu.addAction("Çıkış")
    act_quit.triggered.connect(on_quit)

    tray.setContextMenu(tray_menu)
    tray.activated.connect(lambda reason: window.expand_to_full() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()

    # Restore desktop icons on quit
    app.aboutToQuit.connect(lambda: win32_helper.set_desktop_icons_visible(True))

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
