# DropStop

**Temporarily pause Dropbox syncing for a specified duration.**

DropStop is a Windows system tray utility that lets you pause and resume Dropbox via the tray icon or command line. After the pause duration expires, Dropbox automatically restarts.

## Features

- **System tray icon** with right-click menu for quick pause/resume
- **Command-line interface** for scripting and quick access
- **Visual indicator** — green icon when Dropbox is running, red when paused
- **Balloon notifications** when pausing/resuming (can be disabled)
- **Status dialog** (double-click tray icon) with live countdown timer
- **Single instance** — CLI commands route to the running tray app via IPC
- **Auto-resume on exit** — if you close DropStop while Dropbox is paused, it restarts Dropbox

## Installation

### Requirements
- Python 3.10+
- Windows 10/11

### Setup
```bash
pip install -r requirements.txt
```

### Build standalone executables
```bash
pip install pyinstaller
build.bat
```
Two executables are produced in `dist\`:

| File | Purpose |
|------|---------|
| `DropStop.exe` | CLI / launcher — prints output, exits immediately |
| `DropStop_tray.exe` | Background tray process — spawned automatically by `DropStop.exe` |

Both files must be kept in the same directory.

## Usage

### Command Line

```
DropStop.exe -t 5        # Pause Dropbox for 5 minutes
DropStop.exe -t .5       # Pause for 30 seconds
DropStop.exe -t 0        # Pause indefinitely
DropStop.exe -r          # Resume Dropbox (overrides any timer)
DropStop.exe -s          # Show current status
DropStop.exe             # Launch tray app (no action)
DropStop.exe -v          # Show version
DropStop.exe -h          # Show help
```

The CLI process exits immediately after sending its command. If no tray instance is running, `DropStop_tray.exe` is spawned as a detached background process so your terminal prompt returns right away.

### System Tray

- **Right-click** — Context menu with preset durations and options
- **Double-click** — Status dialog with live countdown and Pause/Resume buttons

### Tray Menu Options

| Option | Action |
|--------|--------|
| Status... | Open status dialog (default action) |
| Pause 1 minute | Pause Dropbox for 1 minute |
| Pause 5 minutes | Pause Dropbox for 5 minutes |
| Pause 10 minutes | Pause Dropbox for 10 minutes |
| Pause 30 minutes | Pause Dropbox for 30 minutes |
| Pause 1 hour | Pause Dropbox for 1 hour |
| Pause indefinitely | Pause until manually resumed |
| Resume Dropbox | Restart Dropbox immediately |
| Notifications | Toggle balloon notifications on/off |
| About... | Version info |
| Exit | Resume Dropbox (if paused) and close |

## Configuration

Settings are stored in `%APPDATA%\DropStop\config.json`:

```json
{
  "dropbox_path": "C:\\Program Files (x86)\\Dropbox\\Client\\Dropbox.exe",
  "notifications_enabled": true
}
```

On first run, DropStop auto-detects the Dropbox path. If it can't find it, a file browser dialog will appear.

## Running from Source

```bash
python -m dropstop.main
python -m dropstop.main -t 5
python -m dropstop.main -s
python -m dropstop.main -r
```

## Architecture

- **Two-process design**: `DropStop.exe` is a short-lived CLI process; `DropStop_tray.exe` is the long-running background tray process. This keeps the terminal prompt responsive and avoids shared-tempdir cleanup issues.
- **IPC**: Localhost TCP socket on port 49152 — subsequent CLI calls route to the running tray instance (no firewall prompt).
- **Single instance**: If a tray is already running, CLI commands are forwarded via IPC and the CLI exits immediately.
- **Timer**: Background thread with cancelable timer.
- **Tray**: pystray with Windows notification support.
- **Tkinter thread safety**: All dialogs run on a single dedicated Tk thread via a shared `Tk` root, preventing `Tcl_AsyncDelete` crashes on repeated opens.
- **Process management**: psutil for finding/killing Dropbox, subprocess for restarting.

## License

MIT
