"""Entry point for the DropStop_tray executable.

This is spawned detached by DropStop.exe when no running instance exists.
It owns the system tray icon and the IPC server for the lifetime of the session.
"""
import argparse
import sys

from dropstop.config import load_config, get_dropbox_path
from dropstop.timer_mgr import TimerManager
from dropstop.ipc import IPCServer, IPC_PORT
from dropstop.tray import DropStopTray
from dropstop.dialog import StatusDialog, show_about
from dropstop.process_mgr import stop_dropbox, start_dropbox, is_dropbox_running
from dropstop import __version__


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-t", "--time", type=float, dest="time", default=None)
    parser.add_argument("-r", "--resume", action="store_true")
    args, _ = parser.parse_known_args()

    # Running as the background tray process — no console needed.
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.FreeConsole()

    from dropstop.main import App, _format_duration

    command = None
    if args.time is not None:
        command = {"action": "pause", "minutes": args.time}
    elif args.resume:
        command = {"action": "resume"}

    app = App()
    app.run(initial_command=command)


if __name__ == "__main__":
    main()
