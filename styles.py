def get_theme_qss(opacity: float = 0.88) -> str:
    alpha = max(0.20, min(1.0, opacity))
    header_alpha = max(0.25, min(1.0, alpha + 0.05))

    return f"""
/* Main Container */
QFrame#MainContainer {{
    background-color: rgba(20, 22, 30, {alpha:.2f});
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
}}

/* Collapsed Mini Applications Bar */
QFrame#ApplicationsBar {{
    background-color: rgba(18, 20, 28, {alpha:.2f});
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 7px;
    padding: 2px 10px;
}}

QFrame#ApplicationsBar:hover {{
    background-color: rgba(30, 34, 48, {min(1.0, alpha + 0.10):.2f});
    border: 1px solid rgba(59, 130, 246, 0.5);
}}

QLabel#ApplicationsBarTitle {{
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif;
}}

/* Header */
QFrame#HeaderBar {{
    background-color: rgba(28, 30, 42, {header_alpha:.2f});
    border-top-left-radius: 11px;
    border-top-right-radius: 11px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 3px 6px;
}}

QLabel#TitleLabel {{
    color: #f1f2f6;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    font-family: 'Segoe UI Variable', 'Segoe UI', system-ui, sans-serif;
}}

QLabel#ItemCountLabel {{
    color: #8a909d;
    font-size: 10px;
    font-weight: 500;
}}

/* Header Action Buttons */
QToolButton.HeaderBtn {{
    background-color: transparent;
    color: #c0c4cc;
    border: none;
    border-radius: 5px;
    padding: 2px 5px;
    font-size: 12px;
    font-weight: 600;
}}

QToolButton.HeaderBtn:hover {{
    background-color: rgba(255, 255, 255, 0.12);
    color: #ffffff;
}}

QToolButton.HeaderBtn:pressed {{
    background-color: rgba(255, 255, 255, 0.20);
}}

/* Search Bar */
QLineEdit#SearchBar {{
    background-color: rgba(14, 16, 22, 0.90);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 6px;
    color: #f5f6fa;
    padding: 4px 8px;
    font-size: 11px;
    selection-background-color: #3b82f6;
}}

QLineEdit#SearchBar:focus {{
    border: 1px solid #3b82f6;
    background-color: rgba(14, 16, 22, 0.98);
}}

/* Category Tabs */
QFrame#TabBar {{
    background-color: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding: 1px 4px;
}}

QPushButton.CategoryTab {{
    background-color: transparent;
    color: #8c93a0;
    border: none;
    border-radius: 5px;
    padding: 3px 6px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.2px;
}}

QPushButton.CategoryTab:hover {{
    background-color: rgba(255, 255, 255, 0.08);
    color: #e2e4e9;
}}

QPushButton.CategoryTab[active="true"] {{
    background-color: #3b82f6;
    color: #ffffff;
}}

/* High-performance QListView */
QListView#FileListView {{
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px 4px 0px 4px;
}}

QListView#FileListView::item {{
    color: #f1f2f6;
    border-radius: 6px;
    padding: 4px;
    margin: 2px;
}}

QListView#FileListView::item:hover {{
    background-color: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.15);
}}

QListView#FileListView::item:selected {{
    background-color: rgba(59, 130, 246, 0.35);
    border: 1px solid #3b82f6;
}}

/* Modern Slim Scrollbar */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 4px;
    margin: 2px 0 2px 0;
    border-radius: 2px;
}}

QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.22);
    min-height: 20px;
    border-radius: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: rgba(255, 255, 255, 0.45);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

/* Context Menu */
QMenu {{
    background-color: rgba(26, 28, 38, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    color: #f1f2f6;
    padding: 5px 20px 5px 10px;
    border-radius: 5px;
    font-size: 11px;
}}

QMenu::item:selected {{
    background-color: #3b82f6;
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 3px 4px;
}}
"""
