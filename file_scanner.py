import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import OrderedDict
from threading import Thread, Lock
from queue import Queue

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QFileInfo
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtGui import QIcon
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from config import get_desktop_paths

CATEGORIES = {
    "all": {
        "title": "Tümü",
        "exts": set()
    },
    "apps": {
        "title": "Uygulamalar",
        "exts": {".exe", ".lnk", ".bat", ".cmd", ".url", ".msi", ".vbs", ".ps1"}
    },
    "docs": {
        "title": "Belgeler",
        "exts": {".doc", ".docx", ".pdf", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".csv", ".rtf", ".md", ".odt", ".epub"}
    },
    "media": {
        "title": "Medya",
        "exts": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico", ".svg",
                 ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".flac",
                 ".zip", ".rar", ".7z", ".tar", ".gz", ".iso"}
    },
    "code": {
        "title": "Geliştirme",
        "exts": {".py", ".js", ".ts", ".html", ".css", ".json", ".sql", ".c", ".cpp", ".h", ".cs", ".java", ".xml", ".yaml", ".yml"}
    },
    "dirs": {
        "title": "Klasörler",
        "exts": set()
    }
}

@dataclass
class DesktopItem:
    name: str
    path: str
    ext: str
    category: str
    is_dir: bool
    size: int
    modified_time: float
    icon: Optional[QIcon] = None

class LRUIconCache:
    """Fixed-size thread-safe LRU Icon cache to guarantee < 30MB RAM footprint."""
    def __init__(self, capacity: int = 250):
        self.capacity = capacity
        self.cache: OrderedDict[str, QIcon] = OrderedDict()
        self.lock = Lock()

    def get(self, key: str) -> Optional[QIcon]:
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key: str, icon: QIcon):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)
            self.cache[key] = icon

class DebouncedWatchdogHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_any_event(self, event):
        if "desktop.ini" in event.src_path or event.src_path.endswith(".tmp"):
            return
        self.callback()

class FileScanner(QObject):
    items_updated = pyqtSignal(list)
    icon_resolved = pyqtSignal(str, QIcon)

    def __init__(self, custom_path: Optional[str] = None):
        super().__init__()
        self.custom_path = custom_path
        self.icon_provider = QFileIconProvider()
        self.lru_cache = LRUIconCache(capacity=300)
        self.observer = None
        self._items: List[DesktopItem] = []

        # Debounce timer for zero-CPU event coalescing
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(350)
        self._debounce_timer.timeout.connect(self._do_scan_and_emit)

    def get_category_for_file(self, ext: str, is_dir: bool) -> str:
        if is_dir:
            return "dirs"
        for cat_key, cat_data in CATEGORIES.items():
            if ext in cat_data["exts"]:
                return cat_key
        return "docs"

    def scan_desktop(self) -> List[DesktopItem]:
        target_dirs = [Path(self.custom_path)] if self.custom_path else get_desktop_paths()
        items = []
        seen_names = set()

        for d in target_dirs:
            p_str = str(d)
            if not os.path.isdir(p_str):
                continue

            try:
                with os.scandir(p_str) as entries:
                    for entry in entries:
                        name = entry.name
                        if name.lower() == "desktop.ini" or name.startswith("~$"):
                            continue
                        if name in seen_names:
                            continue
                        seen_names.add(name)

                        try:
                            is_dir = entry.is_dir(follow_symlinks=False)
                            stat = entry.stat(follow_symlinks=False)
                            size = stat.st_size if not is_dir else 0
                            mtime = stat.st_mtime
                        except Exception:
                            is_dir = False
                            size = 0
                            mtime = 0

                        ext = os.path.splitext(name)[1].lower()
                        cat = self.get_category_for_file(ext, is_dir)
                        icon = self.get_file_icon(entry.path, ext, is_dir, mtime)

                        display_name = name
                        if ext in (".lnk", ".url"):
                            display_name = os.path.splitext(name)[0]

                        items.append(DesktopItem(
                            name=display_name,
                            path=entry.path,
                            ext=ext,
                            category=cat,
                            is_dir=is_dir,
                            size=size,
                            modified_time=mtime,
                            icon=icon
                        ))
            except Exception as e:
                print(f"Error scanning {p_str}: {e}")

        self._items = items
        return items

    def get_file_icon(self, path: str, ext: str, is_dir: bool, mtime: float) -> QIcon:
        cache_key = f"{path}_{mtime}" if ext in (".exe", ".lnk", ".url") else f"{ext}_{is_dir}"
        cached = self.lru_cache.get(cache_key)
        if cached:
            return cached

        try:
            info = QFileInfo(path)
            icon = self.icon_provider.icon(info)
            if not icon.isNull():
                self.lru_cache.put(cache_key, icon)
                return icon
        except Exception:
            pass

        fallback = self.icon_provider.icon(
            QFileIconProvider.IconType.Folder if is_dir else QFileIconProvider.IconType.File
        )
        self.lru_cache.put(cache_key, fallback)
        return fallback

    def start_watcher(self):
        try:
            self.observer = Observer()
            handler = DebouncedWatchdogHandler(self._on_fs_trigger)
            target_dirs = [Path(self.custom_path)] if self.custom_path else get_desktop_paths()
            for d in target_dirs:
                if d.exists():
                    self.observer.schedule(handler, str(d), recursive=False)
            self.observer.daemon = True
            self.observer.start()
        except Exception as e:
            print(f"Watchdog error: {e}")

    def stop_watcher(self):
        if self.observer and self.observer.is_alive():
            try:
                self.observer.stop()
                self.observer.join(timeout=0.5)
            except Exception:
                pass

    def _on_fs_trigger(self):
        self._debounce_timer.start()

    def _do_scan_and_emit(self):
        items = self.scan_desktop()
        self.items_updated.emit(items)
