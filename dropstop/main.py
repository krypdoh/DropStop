import argparse
import sys
import os

from dropstop import __version__
from dropstop.config import load_config, save_config, get_dropbox_path
from dropstop.process_mgr import stop_dropbox, start_dropbox, is_dropbox_running
from dropstop.timer_mgr import TimerManager
from dropstop.ipc import IPCServer, send_command, IPC_PORT
from dropstop.tray import DropStopTray
from dropstop.dialog import StatusDialog, show_about


class App:
    """Main application controller."""

    def __init__(self):
        self.config = load_config()
        self.timer_mgr = TimerManager(on_expire_callback=self._on_timer_expire)
        self.tray = DropStopTray(self)
        self.ipc_server = None
        self.status_dialog = StatusDialog(self)
        self._dropbox_path = None

    def run(self, initial_command=None):
        """Start the tray application."""
        self._dropbox_path = get_dropbox_path(self.config)
        if not self._dropbox_path:
            print("ERROR: Could not locate Dropbox.exe. Exiting.", file=sys.stderr)
            sys.exit(1)

        # Start IPC server
        try:
            self.ipc_server = IPCServer(handler=self._handle_ipc_command)
            self.ipc_server.start()
        except OSError:
            print(
                f"ERROR: Could not bind to port {IPC_PORT}. "
                "Another application may be using it. Exiting.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Store initial command to execute once tray is ready
        self._initial_command = initial_command

        # Run tray (blocking)
        self.tray.start()

    def on_tray_ready(self):
        """Called when tray icon is visible and ready."""
        # Execute initial command if any
        if self._initial_command:
            cmd = self._initial_command
            if cmd["action"] == "pause":
                self.do_pause(cmd["minutes"])
            elif cmd["action"] == "resume":
                self.do_resume()
            elif cmd["action"] == "status":
                state = self.timer_mgr.get_state()
                running = is_dropbox_running()
                _print_status({
                    "dropbox_running": running,
                    "timer_state": state["status"],
                    "indefinite": state["indefinite"],
                    "remaining": state["remaining"],
                })

    def do_pause(self, minutes):
        """Pause Dropbox for the specified minutes."""
        stop_dropbox()
        self.timer_mgr.pause(minutes)
        self.tray.update()

        if minutes == 0:
            self.tray.notify("Pausing Dropbox indefinitely")
        else:
            self.tray.notify(f"Pausing Dropbox for {_format_duration(minutes)}")

    def do_resume(self):
        """Resume Dropbox."""
        self.timer_mgr.resume()
        if self._dropbox_path:
            start_dropbox(self._dropbox_path)
        self.tray.update()
        self.tray.notify("Resuming Dropbox")

    def show_status_dialog(self):
        """Show the status dialog window."""
        self.status_dialog.show()

    def show_about_dialog(self):
        """Show the about dialog."""
        show_about()

    def shutdown(self):
        """Clean shutdown: resume Dropbox if paused, then exit."""
        if self.timer_mgr.is_paused:
            self.timer_mgr.resume()
            if self._dropbox_path:
                start_dropbox(self._dropbox_path)

        if self.ipc_server:
            self.ipc_server.stop()
        self.tray.stop()

    def _on_timer_expire(self):
        """Called when the pause timer expires."""
        if self._dropbox_path:
            start_dropbox(self._dropbox_path)
        self.tray.update()
        self.tray.notify("Resuming Dropbox")

    def _handle_ipc_command(self, command):
        """Handle an IPC command from a CLI invocation."""
        action = command.get("action")

        if action == "pause":
            minutes = command.get("minutes", 5)
            self.do_pause(minutes)
            if minutes == 0:
                return {"status": "ok", "message": "Dropbox paused indefinitely"}
            return {"status": "ok", "message": f"Dropbox paused for {_format_duration(minutes)}"}

        elif action == "resume":
            self.do_resume()
            return {"status": "ok", "message": "Dropbox resumed"}

        elif action == "status":
            state = self.timer_mgr.get_state()
            running = is_dropbox_running()
            return {
                "status": "ok",
                "dropbox_running": running,
                "timer_state": state["status"],
                "indefinite": state["indefinite"],
                "remaining": state["remaining"],
            }

        return {"status": "error", "message": f"Unknown action: {action}"}


def _format_duration(minutes):
    """Format minutes into a human-readable string."""
    if minutes >= 60:
        hours = minutes / 60
        if hours == int(hours):
            return f"{int(hours)} hour{'s' if hours != 1 else ''}"
        return f"{hours:.1f} hours"
    if minutes == int(minutes):
        return f"{int(minutes)} minute{'s' if minutes != 1 else ''}"
    # For fractional minutes, show seconds
    seconds = minutes * 60
    if seconds == int(seconds):
        return f"{int(seconds)} seconds"
    return f"{minutes} minutes"


def _spawn_tray_detached(extra_args=()):
    """Spawn DropStop_tray.exe as a detached background process.

    Looks for DropStop_tray.exe next to the current executable (installed/dist
    layout). Falls back to running tray_main.py via the current interpreter
    for development runs.
    """
    import subprocess
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200

    exe_dir = os.path.dirname(sys.executable)
    tray_exe = os.path.join(exe_dir, "DropStop_tray.exe")
    if os.path.isfile(tray_exe):
        cmd = [tray_exe] + list(extra_args)
    else:
        # Development fallback
        cmd = [sys.executable, "-m", "dropstop.tray_main"] + list(extra_args)

    subprocess.Popen(
        cmd,
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser(
        prog="dropstop",
        description="DropStop - Temporarily pause Dropbox syncing",
    )
    parser.add_argument(
        "-t", "--time",
        type=float,
        metavar="MINUTES",
        help="Pause Dropbox for MINUTES (0 = indefinitely, decimals OK)",
    )
    parser.add_argument(
        "-r", "--resume",
        action="store_true",
        help="Resume Dropbox (overrides any active pause timer)",
    )
    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="Show current status",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"DropStop {__version__}",
    )

    args = parser.parse_args()

    # ── CLI mode ──────────────────────────────────────────────────────────
    command = None
    if args.time is not None:
        if args.time < 0:
            print("ERROR: Time must be >= 0", file=sys.stderr)
            sys.exit(1)
        command = {"action": "pause", "minutes": args.time}
    elif args.resume:
        command = {"action": "resume"}
    elif args.status:
        command = {"action": "status"}

    # Try to send to an existing running instance
    if command:
        try:
            response = send_command(command)
            if response.get("status") == "ok":
                if "message" in response:
                    print(response["message"])
                elif command["action"] == "status":
                    _print_status(response)
            else:
                print(f"Error: {response.get('message', 'Unknown error')}", file=sys.stderr)
            sys.exit(0)
        except (ConnectionRefusedError, OSError):
            if command["action"] == "status":
                print("DropStop is not running.")
                sys.exit(0)
            # pause/resume with no running instance: fall through to spawn tray

    # No running instance — spawn DropStop_tray.exe detached and exit immediately.
    extra = []
    if args.time is not None:
        extra += ["-t", str(args.time)]
    elif args.resume:
        extra += ["-r"]
    _spawn_tray_detached(extra)
    sys.exit(0)




def _print_status(response):
    """Print status response to console."""
    running = response.get("dropbox_running", False)
    timer_state = response.get("timer_state", "unknown")
    indefinite = response.get("indefinite", False)
    remaining = response.get("remaining")

    print(f"Dropbox process: {'Running' if running else 'Stopped'}")
    print(f"DropStop state:  {timer_state.title()}")

    if timer_state == "paused":
        if indefinite:
            print("Duration:        Indefinitely")
        elif remaining is not None:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            print(f"Remaining:       {mins:02d}:{secs:02d}")


if __name__ == "__main__":
    main()
