import tkinter as tk
from tkinter import simpledialog, messagebox
import threading


class _TkThread:
    """Singleton that owns a persistent hidden Tk root in a dedicated thread.

    All Tkinter widgets must be created on this thread. Use call_soon() to
    dispatch callables to it from any other thread.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._ready = threading.Event()
        self._root = None
        t = threading.Thread(target=self._run, daemon=True, name="TkThread")
        t.start()
        self._ready.wait()

    def _run(self):
        self._root = tk.Tk()
        self._root.withdraw()  # hidden; dialogs use Toplevel
        self._ready.set()
        self._root.mainloop()

    def call_soon(self, fn):
        """Schedule fn() to run on the Tk thread (thread-safe)."""
        self._root.after(0, fn)

    @property
    def root(self):
        return self._root


class StatusDialog:
    """Tkinter dialog showing DropStop status with live countdown."""

    def __init__(self, app):
        self.app = app
        self._window = None
        self._update_job = None

    def show(self):
        """Show the status dialog (thread-safe)."""
        _TkThread.get().call_soon(self._show_on_tk_thread)

    def _show_on_tk_thread(self):
        """Must only be called from the Tk thread."""
        if self._window is not None:
            try:
                self._window.lift()
                self._window.focus_force()
                return
            except tk.TclError:
                self._window = None

        self._create_window()

    def _create_window(self):
        """Create the status window as a Toplevel on the shared Tk root."""
        root = _TkThread.get().root
        self._window = tk.Toplevel(root)
        self._window.title("DropStop Status")
        self._window.resizable(False, False)
        self._window.attributes("-topmost", True)

        # Try to set icon
        try:
            from dropstop.icon import save_ico
            import tempfile, os
            ico_path = os.path.join(tempfile.gettempdir(), "dropstop_icon.ico")
            if not os.path.exists(ico_path):
                save_ico(ico_path, color="#CC0000")
            self._window.iconbitmap(ico_path)
        except Exception:
            pass

        # Main frame
        frame = tk.Frame(self._window, padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Status label
        tk.Label(frame, text="Dropbox Status:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self._status_label = tk.Label(frame, text="", font=("Segoe UI", 14, "bold"))
        self._status_label.pack(anchor=tk.W, pady=(2, 10))

        # Timer label
        self._timer_frame = tk.Frame(frame)
        self._timer_frame.pack(anchor=tk.W, fill=tk.X)
        tk.Label(self._timer_frame, text="Time remaining:", font=("Segoe UI", 10)).pack(anchor=tk.W)
        self._timer_label = tk.Label(self._timer_frame, text="", font=("Segoe UI", 12))
        self._timer_label.pack(anchor=tk.W, pady=(2, 10))

        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self._pause_btn = tk.Button(
            btn_frame, text="Pause...", width=10, command=self._on_pause
        )
        self._pause_btn.pack(side=tk.LEFT, padx=(0, 5))

        self._resume_btn = tk.Button(
            btn_frame, text="Resume", width=10, command=self._on_resume
        )
        self._resume_btn.pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(btn_frame, text="Close", width=10, command=self._on_close).pack(side=tk.RIGHT)

        # Initial update and start refresh loop
        self._update_display()

        # Center window on screen
        self._window.update_idletasks()
        w = self._window.winfo_width()
        h = self._window.winfo_height()
        x = (self._window.winfo_screenwidth() // 2) - (w // 2)
        y = (self._window.winfo_screenheight() // 2) - (h // 2)
        self._window.geometry(f"+{x}+{y}")

        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _update_display(self):
        """Update the status display."""
        if self._window is None:
            return

        try:
            state = self.app.timer_mgr.get_state()

            if state["status"] == "running":
                self._status_label.config(text="Running", fg="#228B22")
                self._timer_label.config(text="—")
                self._pause_btn.config(state=tk.NORMAL)
                self._resume_btn.config(state=tk.DISABLED)
            else:
                self._status_label.config(text="Paused", fg="#CC0000")
                self._pause_btn.config(state=tk.DISABLED)
                self._resume_btn.config(state=tk.NORMAL)

                if state["indefinite"]:
                    self._timer_label.config(text="Indefinitely")
                elif state["remaining"] is not None:
                    remaining = state["remaining"]
                    mins = int(remaining // 60)
                    secs = int(remaining % 60)
                    self._timer_label.config(text=f"{mins:02d}:{secs:02d}")
                else:
                    self._timer_label.config(text="—")

            # Schedule next update
            self._update_job = self._window.after(1000, self._update_display)
        except tk.TclError:
            # Window was destroyed
            self._window = None

    def _on_pause(self):
        """Prompt user for minutes and pause."""
        minutes = simpledialog.askfloat(
            "Pause Dropbox",
            "Enter number of minutes to pause\n(0 = indefinitely):",
            minvalue=0,
            parent=self._window,
        )
        if minutes is not None:
            self.app.do_pause(minutes)
            self._update_display()

    def _on_resume(self):
        """Resume Dropbox."""
        self.app.do_resume()
        self._update_display()

    def _on_close(self):
        """Close the dialog."""
        if self._update_job:
            self._window.after_cancel(self._update_job)
        self._window.destroy()
        self._window = None


def show_about():
    """Show the About dialog (thread-safe)."""
    _TkThread.get().call_soon(_show_about_on_tk_thread)


def _show_about_on_tk_thread():
    root = _TkThread.get().root
    messagebox.showinfo(
        "About DropStop",
        "DropStop v1.0.0\n\n"
        "Dropbox Pause Utility\n\n"
        "Temporarily pause Dropbox syncing\n"
        "for a specified duration.\n\n"
        "© 2026",
        parent=root,
    )
