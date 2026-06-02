import subprocess
import psutil

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008


def is_dropbox_running():
    """Check if any Dropbox.exe process is running."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == "dropbox.exe":
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False


def stop_dropbox():
    """Terminate all Dropbox.exe processes. Returns True if any were killed."""
    killed = False
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == "dropbox.exe":
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except psutil.TimeoutExpired:
                    proc.kill()
                killed = True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return killed


def start_dropbox(dropbox_path):
    """Start Dropbox as a detached process."""
    subprocess.Popen(
        [dropbox_path],
        creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
        close_fds=True,
    )
