"""Persistence and data-validation helpers for Foci.

Everything in this module is plain Python with no pygame dependency, so it can
be imported and unit-tested without opening a window.  ``main.py`` wraps these
functions with the app's live defaults (theme list, day hours, font paths).
"""

import datetime
import json
import os
import sys

APP_NAME = "Foci"
DATE_FORMAT = "%Y-%m-%d"

DEFAULT_EVENT_COLOR = [181, 234, 215]
MIN_EVENT_MINUTES = 15
MAX_EVENT_MINUTES = 24 * 60


# --- Paths -----------------------------------------------------------------

def app_root():
    """Directory that holds the bundled read-only resources (fonts, icons, music).

    In a PyInstaller build this is the temporary extraction folder; when running
    from source it is the folder containing this file (not the current working
    directory, so ``python path/to/main.py`` works from anywhere).
    """
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return bundle_dir
    return os.path.dirname(os.path.abspath(__file__))


def is_frozen():
    return bool(getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", None))


def platform_data_dir(app_name=APP_NAME, platform=None, environ=None):
    """Per-user writable directory for app data on the current OS."""
    platform = platform or sys.platform
    environ = os.environ if environ is None else environ
    home = os.path.expanduser("~")

    if platform.startswith("win"):
        base = environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
    elif platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return os.path.join(base, app_name)


def user_data_dir(environ=None):
    """Where user files (events, todos, settings, coins, OAuth token) live.

    Resolution order:
      1. ``FOCI_DATA_DIR`` environment variable, if set.
      2. The platform data directory when running as a packaged executable
         (the PyInstaller temp folder is deleted on exit, so data must not be
         written there).
      3. ``assets/`` next to the source when running from a checkout, which is
         where Foci has always kept its JSON files.
    """
    environ = os.environ if environ is None else environ
    override = environ.get("FOCI_DATA_DIR")
    if override:
        return os.path.abspath(os.path.expanduser(override))
    if is_frozen():
        return platform_data_dir(environ=environ)
    return os.path.join(app_root(), "assets")


# --- JSON I/O ----------------------------------------------------------------

def write_json_file(path, data, *, indent=2, ensure_ascii=True):
    """Atomically write ``data`` as JSON (write to a temp file, then rename)."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    os.replace(temp_path, path)


def read_json_file(path, default=None):
    """Read JSON from ``path``; return ``default`` if missing or unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except (OSError, ValueError) as e:  # JSONDecodeError and UnicodeDecodeError are ValueErrors
        print(f"Warning: could not read {os.path.basename(path)} ({e}). Using defaults.")
        return default


# --- Small helpers -----------------------------------------------------------

def safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(val, lo, hi):
    return max(lo, min(val, hi))


# --- Settings ----------------------------------------------------------------

def sanitize_settings(loaded_settings, defaults, theme_names, resolve_font=None):
    """Merge ``loaded_settings`` over ``defaults`` and coerce every field to a valid value."""
    sanitized = dict(defaults)
    if isinstance(loaded_settings, dict):
        sanitized.update(loaded_settings)

    theme = sanitized.get("theme")
    if theme not in theme_names:
        theme = defaults["theme"]

    start_hour = _clamp(safe_int(sanitized.get("start_hour"), defaults["start_hour"]), 0, 12)
    end_hour = _clamp(safe_int(sanitized.get("end_hour"), defaults["end_hour"]), 13, 23)
    if end_hour <= start_hour:
        start_hour, end_hour = defaults["start_hour"], defaults["end_hour"]

    hour_height = _clamp(safe_int(sanitized.get("hour_height"), defaults["hour_height"]), 30, 80)
    font_path = sanitized.get("font_path")
    if resolve_font is not None:
        font_path = resolve_font(font_path)

    return {
        "theme": theme,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "sounds_on": bool(sanitized.get("sounds_on", defaults["sounds_on"])),
        "hour_height": hour_height,
        "confetti_on": bool(sanitized.get("confetti_on", defaults["confetti_on"])),
        "font_path": font_path,
    }


# --- Events ------------------------------------------------------------------

def sanitize_event(raw_event, default_hour=5):
    """Return a cleaned copy of a calendar event dict, or ``None`` if it is unusable."""
    if not isinstance(raw_event, dict):
        return None

    event = dict(raw_event)
    event["title"] = str(event.get("title") or "Untitled")
    event["hour"] = _clamp(safe_int(event.get("hour", default_hour), default_hour), 0, 23)
    event["minute"] = _clamp(safe_int(event.get("minute", 0), 0), 0, 59)
    event["duration"] = _clamp(
        safe_int(event.get("duration", 60), 60), MIN_EVENT_MINUTES, MAX_EVENT_MINUTES
    )
    event["done"] = bool(event.get("done", False))

    color = event.get("color")
    if not (
        isinstance(color, (list, tuple))
        and len(color) == 3
        and all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255 for c in color)
    ):
        color = DEFAULT_EVENT_COLOR
    event["color"] = list(color)

    event["icon"] = max(0, safe_int(event.get("icon", 0), 0))

    google_id = event.get("google_id")
    if google_id is not None and not isinstance(google_id, str):
        event.pop("google_id", None)

    return event


def sanitize_events_by_date(raw_events, default_hour=5):
    """Clean the ``{"YYYY-MM-DD": [event, ...]}`` mapping stored in events.json."""
    if not isinstance(raw_events, dict):
        return {}
    cleaned = {}
    for date_key, date_events in raw_events.items():
        if not isinstance(date_key, str):
            continue
        day = []
        if isinstance(date_events, list):
            for raw_event in date_events:
                event = sanitize_event(raw_event, default_hour)
                if event is not None:
                    day.append(event)
        cleaned[date_key] = day
    return cleaned


# --- To-dos ------------------------------------------------------------------

def sanitize_todos(items):
    """Clean the nested to-do tree (todos and folders with ``children``)."""
    if not isinstance(items, list):
        return []

    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "folder":
            cleaned.append({
                "type": "folder",
                "name": str(item.get("name") or "Untitled Folder"),
                "is_open": bool(item.get("is_open", False)),
                "children": sanitize_todos(item.get("children", [])),
            })
        else:
            todo_item = {
                "type": "todo",
                "title": str(item.get("title") or "Untitled To-do"),
                "done": bool(item.get("done", False)),
            }
            if isinstance(item.get("tag"), str):
                todo_item["tag"] = item["tag"]
            if isinstance(item.get("date"), str):
                todo_item["date"] = item["date"]
            cleaned.append(todo_item)
    return cleaned


def schedule_todo(todo, when, today=None):
    """Apply a context-menu choice ("today", "tomorrow" or "someday") to a to-do in place."""
    today = today or datetime.date.today()
    if when == "today":
        todo["date"] = today.strftime(DATE_FORMAT)
        todo["tag"] = "today"
    elif when == "tomorrow":
        todo["date"] = (today + datetime.timedelta(days=1)).strftime(DATE_FORMAT)
        todo["tag"] = "tmr"
    elif when == "someday":
        todo.pop("date", None)
        todo.pop("tag", None)
    else:
        raise ValueError(f"unknown schedule option: {when!r}")
    return todo


def roll_todo_tags(items, today=None):
    """Advance relative date tags so they stay truthful as days pass.

    * a "tmr" to-do whose date has arrived becomes "today"
    * a "today"/"tmr" to-do whose date is in the past becomes "on <Weekday>"

    Folders are walked recursively, so to-dos filed inside folders roll over too.
    """
    today = today or datetime.date.today()
    for item in items:
        if item.get("type") == "folder":
            roll_todo_tags(item.get("children", []), today)
            continue

        tag = item.get("tag")
        if tag not in ("today", "tmr") or "date" not in item:
            continue
        try:
            todo_date = datetime.datetime.strptime(item["date"], DATE_FORMAT).date()
        except (TypeError, ValueError):
            continue  # malformed date: leave the item alone

        if todo_date < today:
            item["tag"] = f"on {todo_date.strftime('%a')}"
        elif tag == "tmr" and todo_date == today:
            item["tag"] = "today"
    return items


def has_completed_todos(items):
    """True if any to-do in the tree (folders included) is checked off."""
    for item in items:
        if item.get("type") == "folder":
            if has_completed_todos(item.get("children", [])):
                return True
        elif item.get("done"):
            return True
    return False


def remove_completed_todos(items):
    """Return a copy of the tree without checked-off to-dos; folders are kept."""
    kept = []
    for item in items:
        if item.get("type") == "folder":
            folder = dict(item)
            folder["children"] = remove_completed_todos(item.get("children", []))
            kept.append(folder)
        elif not item.get("done"):
            kept.append(item)
    return kept


def todo_tag_label(item, today=None):
    """Short label shown on a to-do's date pill, or ``None`` if it has no tag.

    Returns ``(label, is_overdue)``.
    """
    tag = item.get("tag")
    if not isinstance(tag, str) or not tag:
        return None
    today = today or datetime.date.today()
    overdue = False
    date_str = item.get("date")
    if isinstance(date_str, str):
        try:
            overdue = (
                datetime.datetime.strptime(date_str, DATE_FORMAT).date() < today
                and not item.get("done")
            )
        except ValueError:
            pass
    labels = {"today": "Today", "tmr": "Tomorrow"}
    return labels.get(tag, tag), overdue
