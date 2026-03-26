import sys
import threading
import webbrowser

from tracker import ActivityTracker
from storage import DataStorage
from tray import TrayIcon
from server import DashboardServer


class WinWellbeingApp:
    def __init__(self):
        self.storage = DataStorage()
        self.tracker = ActivityTracker(self.storage)
        self.server = DashboardServer(self.storage)
        self.tray = TrayIcon(
            on_open=self.open_dashboard,
            on_quit=self.quit
        )
        self._running = False

    def run(self):
        self._running = True

        tracker_thread = threading.Thread(target=self.tracker.start, daemon=True)
        tracker_thread.start()

        server_thread = threading.Thread(target=self.server.start, daemon=True)
        server_thread.start()

        self.open_dashboard()
        self.tray.run()

    def open_dashboard(self):
        webbrowser.open("http://localhost:7331")

    def quit(self):
        self._running = False
        self.tracker.stop()
        self.server.stop()
        sys.exit(0)