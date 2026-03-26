import time
import ctypes
import datetime
import platform

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import win32gui
        import win32process
        import psutil
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
else:
    WIN32_AVAILABLE = False


def get_idle_seconds():
    if not IS_WINDOWS:
        return 0
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_ulong)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    except Exception:
        return 0


def get_active_window():
    if not WIN32_AVAILABLE:
        import random
        apps = [
            ("chrome", "YouTube - How to build apps"),
            ("chrome", "GitHub - my-project"),
            ("Code", "main.py - WinWellbeing"),
            ("Code", "tracker.py - WinWellbeing"),
            ("Slack", "general - MyTeam"),
            ("Outlook", "Inbox - Work Email"),
            ("Excel", "Q4 Report.xlsx"),
            ("spotify", "Now Playing - Lofi Beats"),
        ]
        return random.choice(apps)
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        app_name = proc.name().replace(".exe", "")
        return app_name, title
    except Exception:
        return None, None


APP_CATEGORIES = {
    "chrome": "browser", "firefox": "browser", "msedge": "browser",
    "brave": "browser", "opera": "browser",
    "Code": "dev", "devenv": "dev", "pycharm64": "dev",
    "idea64": "dev", "webstorm64": "dev", "notepad++": "dev",
    "WindowsTerminal": "dev", "cmd": "dev",
    "Slack": "communication", "Teams": "communication",
    "discord": "communication", "zoom": "communication", "Outlook": "communication",
    "Excel": "productivity", "WINWORD": "productivity",
    "POWERPNT": "productivity", "onenote": "productivity", "notion": "productivity",
    "spotify": "entertainment", "vlc": "entertainment",
    "explorer": "system", "taskmgr": "system",
}

CATEGORY_COLORS = {
    "browser":       "#6c8ef7",
    "dev":           "#a78bfa",
    "communication": "#34d399",
    "productivity":  "#fbbf24",
    "entertainment": "#f472b6",
    "system":        "#8891aa",
    "other":         "#60a5fa",
}

IDLE_THRESHOLD = 60  # seconds before marking as idle


class ActivityTracker:
    def __init__(self, storage):
        self.storage = storage
        self._running = False
        self._last_app = None
        self._last_title = None
        self._session_start = None

    def start(self):
        self._running = True
        self._session_start = time.time()

        while self._running:
            try:
                idle = get_idle_seconds()
                now = time.time()

                if idle > IDLE_THRESHOLD:
                    if self._last_app and self._session_start:
                        elapsed = now - self._session_start
                        if elapsed >= 1:
                            self._flush(elapsed)
                    self._last_app = None
                    self._last_title = None
                    self._session_start = None
                    time.sleep(1)
                    continue

                app, title = get_active_window()
                if not app:
                    time.sleep(1)
                    continue

                if app != self._last_app or title != self._last_title:
                    if self._last_app and self._session_start:
                        elapsed = now - self._session_start
                        if elapsed >= 1:
                            self._flush(elapsed)
                    self._last_app = app
                    self._last_title = title
                    self._session_start = now

                time.sleep(1)

            except Exception:
                time.sleep(1)

    def _flush(self, elapsed_seconds):
        now = datetime.datetime.now()
        self.storage.record(
            app=self._last_app,
            title=self._last_title or "",
            seconds=elapsed_seconds,
            timestamp=now,
            category=APP_CATEGORIES.get(self._last_app, "other"),
            color=CATEGORY_COLORS.get(
                APP_CATEGORIES.get(self._last_app, "other"), "#60a5fa"
            )
        )

    def stop(self):
        self._running = False
        if self._last_app and self._session_start:
            elapsed = time.time() - self._session_start
            if elapsed >= 1:
                self._flush(elapsed)