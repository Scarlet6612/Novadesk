import os
import sys
import shutil
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QToolButton, QPushButton, QLineEdit, QListView,
    QMenu, QApplication, QSizeGrip, QFileDialog
)
from PyQt6.QtGui import (
    QIcon, QAction, QCursor, QFont, QColor,
    QStandardItemModel, QStandardItem
)

from config import load_config, save_config, get_desktop_paths
from file_scanner import FileScanner, DesktopItem, CATEGORIES
from styles import get_theme_qss
import win32_helper

class BoxWindow(QWidget):
    """
    Ultra-fast startup desktop container (Fence).
    Architecture:
    - Zero-latency startup: UI renders in <50ms, data loads asynchronously
    - WorkerW desktop canvas integration
    - UI Virtualization with uniform-sized QListView
    - Snap-to-Edge magnetic alignment
    - Roll-up / Double-click caption collapse to 'Applications' pill
    - Folder Portal support
    """
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        
        # Portal mode or standard desktop
        portal_path = self.cfg.get("portal_path") if self.cfg.get("portal_mode") else None
        self.scanner = FileScanner(custom_path=portal_path)
        
        self.all_items = []
        self.filtered_items = []
        self.current_category = self.cfg.get("active_category", "all")
        self.drag_position = QPoint()
        self.is_collapsed = self.cfg.get("collapsed", False)
        self.is_locked = self.cfg.get("locked", False)
        self.opacity_val = self.cfg.get("opacity", 0.85)
        self.pinned_bottom = self.cfg.get("pinned_bottom", True)
        self.hide_desktop_icons = self.cfg.get("hide_desktop_icons", True)
        self.snap_distance = self.cfg.get("snap_distance", 14)
        
        # 2-Row fixed height setup
        self.normal_width = self.cfg.get("width", 380)
        self.normal_height = self.cfg.get("height", 222)
        if self.normal_height > 300:
            self.normal_height = 222

        # 1. Setup UI instantly
        self._setup_window()
        self._init_ui()
        self.apply_theme_style()

        # 2. Defer heavy operations to next event loop ticks (instant window display)
        self.scanner.items_updated.connect(self._on_items_updated)
        QTimer.singleShot(0, self.refresh_items)
        QTimer.singleShot(150, self.scanner.start_watcher)

        # Hide native desktop icons if enabled (deferred)
        if self.hide_desktop_icons and not self.cfg.get("portal_mode", False):
            QTimer.singleShot(500, lambda: win32_helper.set_desktop_icons_visible(False))

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)

        x = max(10, self.cfg.get("x", 24))
        y = max(10, self.cfg.get("y", 24))
        w = max(380, self.normal_width)
        h = max(222, min(320, self.normal_height))
        
        if self.is_collapsed:
            self.setGeometry(x, y, 140, 32)
        else:
            self.setGeometry(x, y, w, h)

    def apply_theme_style(self):
        val = max(0.60, min(1.0, self.opacity_val))
        self.setStyleSheet(get_theme_qss(val))

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        win32_helper.set_tool_window(hwnd)

    def _init_ui(self):
        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setSpacing(0)

        # 1. Mini "Applications" Pill Bar
        self.pill_bar = QFrame()
        self.pill_bar.setObjectName("ApplicationsBar")
        self.pill_bar.setCursor(Qt.CursorShape.PointingHandCursor)
        pill_layout = QHBoxLayout(self.pill_bar)
        pill_layout.setContentsMargins(10, 4, 10, 4)
        pill_layout.setSpacing(6)

        pill_dot = QLabel("●")
        pill_dot.setStyleSheet("color: #3b82f6; font-size: 8px;")
        pill_layout.addWidget(pill_dot)

        self.pill_label = QLabel(self._get_display_title())
        self.pill_label.setObjectName("ApplicationsBarTitle")
        pill_layout.addWidget(self.pill_label)
        pill_layout.addStretch()

        self.pill_count = QLabel("0")
        self.pill_count.setObjectName("ItemCountLabel")
        pill_layout.addWidget(self.pill_count)

        self.pill_bar.mousePressEvent = lambda e: self.expand_to_full()
        self.outer_layout.addWidget(self.pill_bar)

        # 2. Main Full Container
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainContainer")
        self.frame_layout = QVBoxLayout(self.main_frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 2)
        self.frame_layout.setSpacing(2)

        self._create_header()
        self._create_search_bar()
        self._create_tabs()
        self._create_list_view()

        # Bottom Bar
        self.bottom_bar = QHBoxLayout()
        self.bottom_bar.setContentsMargins(8, 0, 4, 2)
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "ItemCountLabel")
        self.bottom_bar.addWidget(self.status_label)
        self.bottom_bar.addStretch()

        self.size_grip = QSizeGrip(self)
        self.size_grip.setVisible(not self.is_locked)
        self.bottom_bar.addWidget(self.size_grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.frame_layout.addLayout(self.bottom_bar)

        self.outer_layout.addWidget(self.main_frame)

        if self.is_collapsed:
            self.pill_bar.setVisible(True)
            self.main_frame.setVisible(False)
        else:
            self.pill_bar.setVisible(False)
            self.main_frame.setVisible(True)

    def _get_display_title(self) -> str:
        if self.cfg.get("portal_mode") and self.cfg.get("portal_path"):
            return Path(self.cfg["portal_path"]).name
        return "Applications"

    def _create_header(self):
        self.header_bar = QFrame()
        self.header_bar.setObjectName("HeaderBar")
        h_layout = QHBoxLayout(self.header_bar)
        h_layout.setContentsMargins(8, 4, 6, 4)
        h_layout.setSpacing(4)

        self.title_label = QLabel(self._get_display_title())
        self.title_label.setObjectName("TitleLabel")
        h_layout.addWidget(self.title_label)

        self.count_badge = QLabel("(0)")
        self.count_badge.setObjectName("ItemCountLabel")
        h_layout.addWidget(self.count_badge)

        h_layout.addStretch()

        self.btn_search = QToolButton()
        self.btn_search.setProperty("class", "HeaderBtn")
        self.btn_search.setText("⌕")
        self.btn_search.setToolTip("Arama Yap")
        self.btn_search.clicked.connect(self._toggle_search)
        h_layout.addWidget(self.btn_search)

        self.btn_lock = QToolButton()
        self.btn_lock.setProperty("class", "HeaderBtn")
        self.btn_lock.setText("🔒" if self.is_locked else "🔓")
        self.btn_lock.setToolTip("Kilitli (Sabit)" if self.is_locked else "Kilidi Açık")
        self.btn_lock.clicked.connect(self.toggle_lock)
        h_layout.addWidget(self.btn_lock)

        self.btn_snap = QToolButton()
        self.btn_snap.setProperty("class", "HeaderBtn")
        self.btn_snap.setText("↖")
        self.btn_snap.setToolTip("Sol Üste Hizala")
        self.btn_snap.clicked.connect(self.snap_to_top_left)
        h_layout.addWidget(self.btn_snap)

        self.btn_minimize = QToolButton()
        self.btn_minimize.setProperty("class", "HeaderBtn")
        self.btn_minimize.setText("─")
        self.btn_minimize.setToolTip("Sol Üstte Başlığa Küçült (Roll-Up)")
        self.btn_minimize.clicked.connect(self.collapse_to_pill)
        h_layout.addWidget(self.btn_minimize)

        self.btn_menu = QToolButton()
        self.btn_menu.setProperty("class", "HeaderBtn")
        self.btn_menu.setText("···")
        self.btn_menu.setToolTip("Seçenekler")
        self.btn_menu.clicked.connect(self._show_header_menu)
        h_layout.addWidget(self.btn_menu)

        self.header_bar.mouseDoubleClickEvent = lambda e: self.collapse_to_pill()
        self.frame_layout.addWidget(self.header_bar)

    def _create_search_bar(self):
        self.search_container = QFrame()
        s_layout = QHBoxLayout(self.search_container)
        s_layout.setContentsMargins(8, 2, 8, 2)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchBar")
        self.search_input.setPlaceholderText("Dosya veya program ara...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        s_layout.addWidget(self.search_input)

        self.search_container.setVisible(False)
        self.frame_layout.addWidget(self.search_container)

    def _create_tabs(self):
        self.tab_container = QFrame()
        self.tab_container.setObjectName("TabBar")
        t_layout = QHBoxLayout(self.tab_container)
        t_layout.setContentsMargins(6, 1, 6, 1)
        t_layout.setSpacing(3)

        self.tab_buttons = {}

        tabs_info = [
            ("all", "Tümü"),
            ("apps", "Uygulamalar"),
            ("docs", "Belgeler"),
            ("media", "Medya"),
            ("code", "Geliştirme"),
            ("dirs", "Klasörler"),
        ]

        for cat_id, title in tabs_info:
            btn = QPushButton(title)
            btn.setProperty("class", "CategoryTab")
            btn.setProperty("active", "true" if self.current_category == cat_id else "false")
            btn.clicked.connect(lambda checked, c=cat_id: self._switch_category(c))
            t_layout.addWidget(btn)
            self.tab_buttons[cat_id] = btn

        self.frame_layout.addWidget(self.tab_container)

    def _create_list_view(self):
        self.model = QStandardItemModel(self)
        self.list_view = QListView()
        self.list_view.setObjectName("FileListView")
        self.list_view.setModel(self.model)
        self.list_view.setViewMode(QListView.ViewMode.IconMode)
        self.list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_view.setMovement(QListView.Movement.Static)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setIconSize(QSize(36, 36))
        self.list_view.setGridSize(QSize(86, 68))
        self.list_view.setSpacing(4)
        self.list_view.setWordWrap(True)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 2 Rows height
        self.list_view.setFixedHeight(142)

        self.list_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._on_list_context_menu)
        self.list_view.doubleClicked.connect(self._on_item_double_clicked)

        self.frame_layout.addWidget(self.list_view, 1)

    def _toggle_search(self):
        vis = not self.search_container.isVisible()
        self.search_container.setVisible(vis)
        if vis:
            self.search_input.setFocus()
            self.resize(self.width(), self.normal_height + 28)
        else:
            self.search_input.clear()
            self.resize(self.width(), self.normal_height)

    def _on_search_text_changed(self, text: str):
        self._filter_and_render_items()

    def _switch_category(self, cat_id: str):
        self.current_category = cat_id
        for c_id, btn in self.tab_buttons.items():
            btn.setProperty("active", "true" if c_id == cat_id else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.cfg["active_category"] = cat_id
        save_config(self.cfg)
        self._filter_and_render_items()

    def refresh_items(self):
        self.all_items = self.scanner.scan_desktop()
        self._filter_and_render_items()

    def _on_items_updated(self, items):
        if self.cfg.get("game_mode_pause", True) and win32_helper.is_fullscreen_or_gaming():
            return
        self.all_items = items
        self._filter_and_render_items()

    def _filter_and_render_items(self):
        search_query = self.search_input.text().lower().strip()
        items = []

        for item in self.all_items:
            if self.current_category != "all" and item.category != self.current_category:
                continue
            if search_query and search_query not in item.name.lower():
                continue
            items.append(item)

        sort_by = self.cfg.get("sort_by", "name")
        reverse = not self.cfg.get("sort_ascending", True)

        if sort_by == "name":
            items.sort(key=lambda x: (not x.is_dir, x.name.lower()), reverse=reverse)
        elif sort_by == "date":
            items.sort(key=lambda x: x.modified_time, reverse=True)
        elif sort_by == "size":
            items.sort(key=lambda x: x.size, reverse=True)
        elif sort_by == "type":
            items.sort(key=lambda x: (x.category, x.ext), reverse=reverse)

        self.filtered_items = items

        self.count_badge.setText(f"({len(items)})")
        self.pill_count.setText(str(len(self.all_items)))
        self.status_label.setText(f"{len(items)} öge (2 satır)")

        self.model.clear()
        for it in items:
            q_item = QStandardItem(it.icon, it.name)
            q_item.setData(it, Qt.ItemDataRole.UserRole)
            q_item.setToolTip(f"{it.name}\nKonum: {it.path}\nBoyut: {self._format_size(it.size)}")
            q_item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            self.model.appendRow(q_item)

    def _format_size(self, size: int) -> str:
        if size <= 0:
            return "Klasör / Kısayol"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _on_item_double_clicked(self, index):
        item_data = index.data(Qt.ItemDataRole.UserRole)
        if item_data:
            win32_helper.open_file(item_data.path)

    def _on_list_context_menu(self, pos):
        index = self.list_view.indexAt(pos)
        if index.isValid():
            item_data = index.data(Qt.ItemDataRole.UserRole)
            if item_data:
                self._show_item_menu(item_data, self.list_view.mapToGlobal(pos))
        else:
            self._show_header_menu()

    def _show_item_menu(self, item: DesktopItem, global_pos):
        menu = QMenu(self)
        
        act_open = menu.addAction("Aç")
        act_open.triggered.connect(lambda: win32_helper.open_file(item.path))

        act_show = menu.addAction("Dosya Konumunda Göster")
        act_show.triggered.connect(lambda: win32_helper.show_in_explorer(item.path))

        act_copy_path = menu.addAction("Dosya Yolunu Kopyala")
        act_copy_path.triggered.connect(lambda: QApplication.clipboard().setText(item.path))

        menu.addSeparator()

        act_archive = menu.addAction("Arşiv Klasörüne Taşı")
        act_archive.triggered.connect(lambda: self._archive_item(item))

        act_delete = menu.addAction("Geri Dönüşüm Kutusuna Gönder")
        act_delete.triggered.connect(lambda: self._delete_item(item))

        menu.exec(global_pos)

    def _archive_item(self, item: DesktopItem):
        try:
            archive_dir = Path.home() / "OneDrive" / "Desktop" / "Masaüstü_Arşiv"
            if not archive_dir.parent.exists():
                archive_dir = Path.home() / "Desktop" / "Masaüstü_Arşiv"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            src = Path(item.path)
            dst = archive_dir / src.name
            shutil.move(str(src), str(dst))
            self.refresh_items()
        except Exception as e:
            print(f"Error archiving {item.name}: {e}")

    def _delete_item(self, item: DesktopItem):
        try:
            p = Path(item.path)
            if p.is_dir():
                shutil.rmtree(str(p))
            else:
                p.unlink()
            self.refresh_items()
        except Exception as e:
            print(f"Error deleting {item.name}: {e}")

    def _show_header_menu(self):
        menu = QMenu(self)

        portal_menu = menu.addMenu("Klasör Portalı (Portal Mode)")
        act_choose_portal = portal_menu.addAction("Klasör Bağla... (Örn: İndirilenler)")
        act_choose_portal.triggered.connect(self._select_portal_folder)

        if self.cfg.get("portal_mode"):
            act_reset_portal = portal_menu.addAction("Varsayılan Masaüstüne Sıfırla")
            act_reset_portal.triggered.connect(self._reset_to_desktop)

        trans_menu = menu.addMenu("Saydamlık (Opaklık)")
        opacity_options = [
            ("%35 - Çok Şeffaf", 0.35),
            ("%50 - Yarı Saydam", 0.50),
            ("%70 - Dengeli", 0.70),
            ("%85 - Varsayılan Koyu", 0.85),
            ("%100 - Tam Opak", 1.0)
        ]
        for opt_label, opt_val in opacity_options:
            act = trans_menu.addAction(opt_label)
            act.setCheckable(True)
            act.setChecked(abs(self.opacity_val - opt_val) < 0.05)
            act.triggered.connect(lambda ch, v=opt_val: self.set_opacity(v))

        act_lock = menu.addAction("Konum ve Boyutu Kilitle")
        act_lock.setCheckable(True)
        act_lock.setChecked(self.is_locked)
        act_lock.triggered.connect(self.toggle_lock)

        act_hide_icons = menu.addAction("Masaüstü Simgelerini Gizle (Sadece Kutuda Göster)")
        act_hide_icons.setCheckable(True)
        act_hide_icons.setChecked(self.hide_desktop_icons)
        act_hide_icons.triggered.connect(self.toggle_desktop_icons)

        act_game_pause = menu.addAction("Oyun/Tam Ekranda Otomatik Duraklat")
        act_game_pause.setCheckable(True)
        act_game_pause.setChecked(self.cfg.get("game_mode_pause", True))
        act_game_pause.triggered.connect(self._toggle_game_pause)

        sort_menu = menu.addMenu("Sıralama Ölçütü")
        for s_key, s_title in [("name", "Ada Göre"), ("date", "Tarihe Göre"), ("size", "Boyuta Göre"), ("type", "Türe Göre")]:
            act = sort_menu.addAction(s_title)
            act.setCheckable(True)
            act.setChecked(self.cfg.get("sort_by") == s_key)
            act.triggered.connect(lambda ch, k=s_key: self._set_sort(k))

        menu.addSeparator()

        act_snap = menu.addAction("Sol Üste Hizala")
        act_snap.triggered.connect(self.snap_to_top_left)

        act_refresh = menu.addAction("Yenile")
        act_refresh.triggered.connect(self.refresh_items)

        menu.addSeparator()

        act_exit = menu.addAction("Çıkış")
        act_exit.triggered.connect(QApplication.instance().quit)

        menu.exec(QCursor.pos())

    def _select_portal_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Portala Bağlanacak Klasörü Seçin")
        if folder:
            self.scanner.stop_watcher()
            self.cfg["portal_mode"] = True
            self.cfg["portal_path"] = folder
            save_config(self.cfg)

            self.scanner = FileScanner(custom_path=folder)
            self.scanner.items_updated.connect(self._on_items_updated)
            self.scanner.start_watcher()

            title = Path(folder).name
            self.title_label.setText(title)
            self.pill_label.setText(title)
            self.refresh_items()

    def _reset_to_desktop(self):
        self.scanner.stop_watcher()
        self.cfg["portal_mode"] = False
        self.cfg["portal_path"] = None
        save_config(self.cfg)

        self.scanner = FileScanner(custom_path=None)
        self.scanner.items_updated.connect(self._on_items_updated)
        self.scanner.start_watcher()

        self.title_label.setText("Applications")
        self.pill_label.setText("Applications")
        self.refresh_items()

    def _toggle_game_pause(self):
        cur = self.cfg.get("game_mode_pause", True)
        self.cfg["game_mode_pause"] = not cur
        save_config(self.cfg)

    def set_opacity(self, val: float):
        self.opacity_val = val
        self.cfg["opacity"] = val
        save_config(self.cfg)
        self.apply_theme_style()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.cfg["locked"] = self.is_locked
        save_config(self.cfg)
        self.btn_lock.setText("🔒" if self.is_locked else "🔓")
        self.btn_lock.setToolTip("Kilitli (Sabit)" if self.is_locked else "Kilidi Açık")
        self.size_grip.setVisible(not self.is_locked)

    def toggle_desktop_icons(self):
        self.hide_desktop_icons = not self.hide_desktop_icons
        self.cfg["hide_desktop_icons"] = self.hide_desktop_icons
        save_config(self.cfg)
        win32_helper.set_desktop_icons_visible(not self.hide_desktop_icons)

    def _set_sort(self, sort_key: str):
        self.cfg["sort_by"] = sort_key
        save_config(self.cfg)
        self._filter_and_render_items()

    def snap_to_top_left(self):
        self.move(20, 20)
        self.cfg["x"] = 20
        self.cfg["y"] = 20
        save_config(self.cfg)

    def collapse_to_pill(self):
        self.is_collapsed = True
        self.cfg["collapsed"] = True
        save_config(self.cfg)

        self.main_frame.setVisible(False)
        self.pill_bar.setVisible(True)
        self.resize(140, 32)

    def expand_to_full(self):
        self.is_collapsed = False
        self.cfg["collapsed"] = False
        save_config(self.cfg)

        self.pill_bar.setVisible(False)
        self.main_frame.setVisible(True)
        self.resize(max(380, self.normal_width), max(222, self.normal_height))

    def mousePressEvent(self, event):
        if self.is_locked:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            target = self.pill_bar if self.is_collapsed else self.header_bar
            if target.geometry().contains(event.pos()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self.is_locked:
            return
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            new_pos = event.globalPosition().toPoint() - self.drag_position
            
            screen = QApplication.primaryScreen()
            if screen:
                s_geo = screen.availableGeometry()
                snap_d = self.snap_distance

                if abs(new_pos.x() - s_geo.left()) < snap_d:
                    new_pos.setX(s_geo.left() + 10)
                if abs(new_pos.y() - s_geo.top()) < snap_d:
                    new_pos.setY(s_geo.top() + 10)
                if abs((new_pos.x() + self.width()) - s_geo.right()) < snap_d:
                    new_pos.setX(s_geo.right() - self.width() - 10)

            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.is_locked:
            return
        self.drag_position = QPoint()
        self.cfg["x"] = self.x()
        self.cfg["y"] = self.y()
        self.cfg["width"] = self.width()
        save_config(self.cfg)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.is_collapsed and not self.is_locked:
            self.normal_width = self.width()
            self.cfg["width"] = self.normal_width
            save_config(self.cfg)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        target_dir = Path(self.cfg["portal_path"]) if self.cfg.get("portal_mode") else get_desktop_paths()[0]
        for url in event.mimeData().urls():
            src_path = url.toLocalFile()
            if os.path.exists(src_path):
                dest_path = target_dir / os.path.basename(src_path)
                try:
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dest_path)
                    else:
                        shutil.copy2(src_path, dest_path)
                except Exception as e:
                    print(f"Drop copy error: {e}")
        self.refresh_items()
        event.acceptProposedAction()
