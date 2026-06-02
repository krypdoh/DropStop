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

### Build standalone .exe
```bash
pip install pyinstaller
build.bat
```
The built executable will be at `dist\DropStop.exe`.

## Usage

### Command Line

```
dropstop -t 5        # Pause Dropbox for 5 minutes
dropstop -t .5       # Pause for 30 seconds
dropstop -t 0        # Pause indefinitely
dropstop -r          # Resume Dropbox (overrides any timer)
dropstop -s          # Show current status
dropstop             # Launch tray app (no action)
dropstop -v          # Show version
```

### System Tray

- **Right-click** — Context menu with preset durations and options
- **Double-click** — Status dialog with live countdown and Pause/Resume buttons

### Tray Menu Options

| Option | Action |
|--------|--------|
| Pause 1 minute | Pause Dropbox for 1 minute |
| Pause 5 minutes | Pause Dropbox for 5 minutes |
| Pause 10 minutes | Pause Dropbox for 10 minutes |
| Pause 30 minutes | Pause Dropbox for 30 minutes |
| Pause 1 hour | Pause Dropbox for 1 hour |
| Pause indefinitely | Pause until manually resumed |
| Resume Dropbox | Restart Dropbox immediately |
| Notifications | Toggle balloon notifications on/off |
| Status... | Open status dialog |
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
python -m dropstop.main -r
```

## Architecture

- **IPC**: Localhost TCP socket on port 49152 (no firewall prompt)
- **Single instance**: Second launch sends command to first via IPC
- **Timer**: Background thread with cancelable timer
- **Tray**: pystray with Windows notification support
- **Process management**: psutil for finding/killing Dropbox, subprocess for restarting

## License

MIT