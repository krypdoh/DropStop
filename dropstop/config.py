import json
import os
import sys

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", ""), "DropStop")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_PATHS = [
    os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Dropbox", "Client", "Dropbox.exe"),
    os.path.join(os.environ.get("PROGRAMFILES", ""), "Dropbox", "Client", "Dropbox.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Dropbox", "Client", "Dropbox.exe"),
]

DEFAULTS = {
    "dropbox_path": None,
    "notifications_enabled": True,
}


def _ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config():
    _ensure_config_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        # Merge with defaults for any missing keys
        for key, val in DEFAULTS.items():
            if key not in data:
                data[key] = val
        return data
    return dict(DEFAULTS)


def save_config(config):
    _ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def find_dropbox_path():
    """Try to find Dropbox.exe automatically."""
    import psutil

    # First check running processes
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == "dropbox.exe":
                return proc.info["exe"]
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

    # Check default install paths
    for path in DEFAULT_PATHS:
        if path and os.path.isfile(path):
            return path

    return None


def prompt_dropbox_path():
    """Show a file dialog to let the user pick Dropbox.exe."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Locate Dropbox.exe",
        filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        initialdir=os.environ.get("PROGRAMFILES(X86)", "C:\\"),
    )
    root.destroy()
    return path if path else None


def get_dropbox_path(config):
    """Get the Dropbox path, auto-detecting or prompting if needed."""
    path = config.get("dropbox_path")
    if path and os.path.isfile(path):
        return path

    # Try auto-detection
    path = find_dropbox_path()
    if path:
        config["dropbox_path"] = path
        save_config(config)
        return path

    # Prompt user
    path = prompt_dropbox_path()
    if path:
        config["dropbox_path"] = path
        save_config(config)
        return path

    return None
