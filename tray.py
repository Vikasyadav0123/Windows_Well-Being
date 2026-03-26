import threading

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


def make_icon_image():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size-2, size-2], fill=(26, 32, 53, 255))
    draw.ellipse([20, 20, 44, 44], fill=(108, 142, 247, 255))
    draw.ellipse([28, 28, 36, 36], fill=(255, 255, 255, 220))
    return img


class TrayIcon:
    def __init__(self, on_open, on_quit):
        self.on_open = on_open
        self.on_quit = on_quit
        self._icon = None

    def run(self):
        if not TRAY_AVAILABLE:
            import time
            print("WinWellbeing running at http://localhost:7331")
            print("Press Ctrl+C to quit.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.on_quit()
            return

        icon_image = make_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", lambda: self.on_open(), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit WinWellbeing", lambda: self._do_quit()),
        )

        self._icon = pystray.Icon(
            "WinWellbeing",
            icon_image,
            "WinWellbeing — tracking active",
            menu
        )
        self._icon.run()

    def _do_quit(self):
        if self._icon:
            self._icon.stop()
        self.on_quit()