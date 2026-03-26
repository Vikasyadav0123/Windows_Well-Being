import json
import datetime
import threading
import time
from pathlib import Path
import os

DATA_DIR = Path(os.path.expanduser("~")) / "AppData" / "Local" / "WinWellbeing" / "data"


class DataStorage:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache = {}
        self._dirty = set()

        def auto_save():
            while True:
                time.sleep(10)
                self.flush()

        t = threading.Thread(target=auto_save, daemon=True)
        t.start()

    def _today(self):
        return datetime.date.today().isoformat()

    def _load_day(self, date_str):
        if date_str in self._cache:
            return self._cache[date_str]
        path = DATA_DIR / f"{date_str}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._cache[date_str] = data
                return data
            except Exception:
                pass
        empty = {"date": date_str, "apps": {}, "timeline": []}
        self._cache[date_str] = empty
        return empty

    def record(self, app, title, seconds, timestamp, category="other", color="#60a5fa"):
        with self._lock:
            date_str = timestamp.date().isoformat()
            hour = timestamp.hour
            data = self._load_day(date_str)

            if app not in data["apps"]:
                data["apps"][app] = {
                    "total_seconds": 0,
                    "category": category,
                    "color": color,
                    "titles": {},
                    "hourly": {str(h): 0 for h in range(24)}
                }

            entry = data["apps"][app]
            entry["total_seconds"] += seconds
            entry["category"] = category
            entry["color"] = color
            entry["hourly"][str(hour)] = entry["hourly"].get(str(hour), 0) + seconds

            clean_title = title.strip()
            if clean_title:
                if clean_title not in entry["titles"]:
                    entry["titles"][clean_title] = 0
                entry["titles"][clean_title] += seconds

            data["timeline"].append({
                "time": timestamp.strftime("%H:%M"),
                "app": app,
                "title": clean_title,
                "seconds": round(seconds),
                "color": color
            })

            if len(data["timeline"]) > 500:
                data["timeline"] = data["timeline"][-500:]

            self._dirty.add(date_str)

    def flush(self):
        with self._lock:
            for date_str in list(self._dirty):
                data = self._cache.get(date_str)
                if data:
                    path = DATA_DIR / f"{date_str}.json"
                    try:
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                    except Exception:
                        pass
            self._dirty.clear()

    def get_day(self, date_str=None):
        if date_str is None:
            date_str = self._today()
        with self._lock:
            return dict(self._load_day(date_str))

    def get_week(self):
        result = []
        today = datetime.date.today()
        for i in range(6, -1, -1):
            d = (today - datetime.timedelta(days=i)).isoformat()
            with self._lock:
                day_data = self._load_day(d)
            total = sum(a["total_seconds"] for a in day_data["apps"].values())
            result.append({"date": d, "total_seconds": total})
        return result

    def list_days(self):
        days = []
        for f in sorted(DATA_DIR.glob("*.json"), reverse=True):
            days.append(f.stem)
        return days