import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".novadesk"
CONFIG_FILE = CONFIG_DIR / "config.json"

def get_desktop_paths():
    """Returns valid desktop paths (OneDrive Desktop + Local Desktop + Public Desktop)."""
    user_home = Path.home()
    paths = []
    
    onedrive_desktop = user_home / "OneDrive" / "Desktop"
    if onedrive_desktop.exists():
        paths.append(onedrive_desktop)
        
    std_desktop = user_home / "Desktop"
    if std_desktop.exists() and std_desktop not in paths:
        paths.append(std_desktop)
        
    public_desktop = Path(os.environ.get("PUBLIC", "C:\\Users\\Public")) / "Desktop"
    if public_desktop.exists() and public_desktop not in paths:
        paths.append(public_desktop)
        
    return paths

DEFAULT_CONFIG = {
    "version": "2.0",
    "x": 20,
    "y": 20,
    "width": 380,
    "height": 222,
    "collapsed": False,
    "locked": False,
    "opacity": 0.85,
    "pinned_bottom": True,
    "hide_desktop_icons": True,
    "active_category": "all",
    "sort_by": "name",
    "sort_ascending": True,
    "snap_distance": 14,
    "game_mode_pause": True,
    "portal_mode": False,
    "portal_path": None,
    "theme": "dark_acrylic",
    "auto_start": True
}

def load_config():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg.update(data)
        except Exception:
            pass

    # Sanitize bounds to prevent window from disappearing or being clipped
    cfg["x"] = max(10, int(cfg.get("x", 24)))
    cfg["y"] = max(10, int(cfg.get("y", 24)))
    cfg["width"] = max(380, int(cfg.get("width", 440)))
    cfg["height"] = max(222, min(350, int(cfg.get("height", 236))))
    if float(cfg.get("opacity", 0.88)) < 0.50:
        cfg["opacity"] = 0.88
    cfg["pinned_bottom"] = False
    return cfg

def save_config(cfg):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
