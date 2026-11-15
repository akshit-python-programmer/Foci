import datetime
import json
import os

import pytest

import foci_store as store

TODAY = datetime.date(2026, 3, 11)  # a Wednesday
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)


def iso(d):
    return d.strftime("%Y-%m-%d")


# --- settings ---------------------------------------------------------------

DEFAULTS = {
    "theme": "Serene Morning",
    "start_hour": 5,
    "end_hour": 23,
    "sounds_on": True,
    "hour_height": 40,
    "confetti_on": True,
    "font_path": "assets/Domine.ttf",
}
THEMES = {"Serene Morning", "Midnight Deep"}


def test_settings_defaults_when_file_missing_or_garbage():
    assert store.sanitize_settings({}, DEFAULTS, THEMES) == DEFAULTS
    assert store.sanitize_settings(["not", "a", "dict"], DEFAULTS, THEMES) == DEFAULTS
    assert store.sanitize_settings(None, DEFAULTS, THEMES) == DEFAULTS


def test_settings_unknown_theme_falls_back():
    out = store.sanitize_settings({"theme": "Neon Vomit"}, DEFAULTS, THEMES)
    assert out["theme"] == "Serene Morning"


def test_settings_values_are_clamped_and_coerced():
    out = store.sanitize_settings(
        {"start_hour": "3", "end_hour": 99, "hour_height": 5, "sounds_on": 0},
        DEFAULTS,
        THEMES,
    )
    assert out["start_hour"] == 3
    assert out["end_hour"] == 23
    assert out["hour_height"] == 30
    assert out["sounds_on"] is False


def test_settings_font_resolver_is_applied():
    out = store.sanitize_settings({"font_path": "x.ttf"}, DEFAULTS, THEMES, lambda p: f"/fonts/{p}")
    assert out["font_path"] == "/fonts/x.ttf"


def test_settings_drop_unknown_keys():
    out = store.sanitize_settings({"evil": True}, DEFAULTS, THEMES)
    assert "evil" not in out


# --- events -----------------------------------------------------------------

def test_event_non_dict_is_rejected():
    assert store.sanitize_event("lunch") is None
    assert store.sanitize_event(None) is None


def test_event_fields_are_repaired():
    ev = store.sanitize_event(
        {"title": "", "hour": "25", "minute": -4, "duration": 2, "color": [1, 2], "icon": "x"}
    )
    assert ev["title"] == "Untitled"
    assert ev["hour"] == 23
    assert ev["minute"] == 0
    assert ev["duration"] == store.MIN_EVENT_MINUTES
    assert ev["color"] == store.DEFAULT_EVENT_COLOR
    assert ev["icon"] == 0
    assert ev["done"] is False


def test_event_bad_hour_uses_default_hour():
    assert store.sanitize_event({"hour": "noon"}, default_hour=8)["hour"] == 8


def test_event_bool_is_not_a_color_channel():
    ev = store.sanitize_event({"color": [True, 0, 0]})
    assert ev["color"] == store.DEFAULT_EVENT_COLOR


def test_event_keeps_extra_fields_and_valid_google_id():
    ev = store.sanitize_event({"title": "Gym", "google_id": "abc", "todo_id": 7})
    assert ev["google_id"] == "abc"
    assert ev["todo_id"] == 7
    assert "google_id" not in store.sanitize_event({"google_id": 123})


def test_events_by_date_skips_junk():
    raw = {"2026-01-01": [{"title": "a"}, "junk"], "2026-01-02": "nope"}
    out = store.sanitize_events_by_date(raw)
    assert [e["title"] for e in out["2026-01-01"]] == ["a"]
    assert out["2026-01-02"] == []
    assert store.sanitize_events_by_date([1, 2]) == {}


# --- todos ------------------------------------------------------------------

def test_todos_tree_is_cleaned_recursively():
    raw = [
        {"type": "folder", "name": "", "children": [{"title": "child", "tag": 5}, 3]},
        "junk",
        {"title": "top", "done": 1, "date": "2026-01-01"},
    ]
    out = store.sanitize_todos(raw)
    assert out[0]["name"] == "Untitled Folder"
    assert out[0]["children"] == [{"type": "todo", "title": "child", "done": False}]
    assert out[1] == {"type": "todo", "title": "top", "done": True, "date": "2026-01-01"}


@pytest.mark.parametrize(
    "when, tag, date",
    [("today", "today", TODAY), ("tomorrow", "tmr", TOMORROW)],
)
def test_schedule_todo_sets_tag_and_date(when, tag, date):
    todo = {"type": "todo", "title": "x"}
    store.schedule_todo(todo, when, today=TODAY)
    assert todo["tag"] == tag
    assert todo["date"] == iso(date)


def test_schedule_tomorrow_keeps_its_tag():
    # Regression: the context menu used to set tag="tmr" and then immediately delete it.
    todo = store.schedule_todo({"title": "x"}, "tomorrow", today=TODAY)
    assert "tag" in todo


def test_schedule_someday_clears_tag_and_date():
    todo = {"title": "x", "tag": "today", "date": iso(TODAY)}
    store.schedule_todo(todo, "someday", today=TODAY)
    assert "tag" not in todo and "date" not in todo


def test_schedule_unknown_option_raises():
    with pytest.raises(ValueError):
        store.schedule_todo({}, "next week")


def test_roll_tags_tomorrow_becomes_today():
    todos = [{"title": "x", "tag": "tmr", "date": iso(TODAY)}]
    store.roll_todo_tags(todos, today=TODAY)
    assert todos[0]["tag"] == "today"


def test_roll_tags_past_items_get_weekday():
    todos = [
        {"title": "a", "tag": "today", "date": iso(YESTERDAY)},
        {"title": "b", "tag": "tmr", "date": iso(YESTERDAY)},
    ]
    store.roll_todo_tags(todos, today=TODAY)
    assert [t["tag"] for t in todos] == ["on Tue", "on Tue"]


def test_roll_tags_leaves_current_and_untagged_items():
    todos = [
        {"title": "a", "tag": "today", "date": iso(TODAY)},
        {"title": "b", "tag": "tmr", "date": iso(TOMORROW)},
        {"title": "c"},
        {"title": "d", "tag": "today", "date": "not-a-date"},
    ]
    before = json.loads(json.dumps(todos))
    store.roll_todo_tags(todos, today=TODAY)
    assert todos == before


def test_roll_tags_reaches_into_folders():
    # Regression: only top-level to-dos used to roll over.
    todos = [
        {
            "type": "folder",
            "name": "Physics",
            "children": [
                {"type": "folder", "name": "Kinematics", "children": [
                    {"title": "deep", "tag": "tmr", "date": iso(TODAY)},
                ]},
                {"title": "shallow", "tag": "today", "date": iso(YESTERDAY)},
            ],
        }
    ]
    store.roll_todo_tags(todos, today=TODAY)
    physics = todos[0]["children"]
    assert physics[0]["children"][0]["tag"] == "today"
    assert physics[1]["tag"] == "on Tue"


def test_completed_todos_in_folders_are_found_and_removed():
    # Regression: "Delete completed" only looked at top-level items.
    todos = [
        {"type": "folder", "name": "F", "children": [
            {"title": "done", "done": True},
            {"title": "open", "done": False},
        ]},
        {"title": "top open", "done": False},
    ]
    assert store.has_completed_todos(todos)
    cleaned = store.remove_completed_todos(todos)
    assert [c["title"] for c in cleaned[0]["children"]] == ["open"]
    assert not store.has_completed_todos(cleaned)
    # the input is not mutated
    assert len(todos[0]["children"]) == 2


def test_tag_label():
    assert store.todo_tag_label({"title": "x"}) is None
    assert store.todo_tag_label({"tag": "today", "date": iso(TODAY)}, TODAY) == ("Today", False)
    assert store.todo_tag_label({"tag": "tmr", "date": iso(TOMORROW)}, TODAY) == ("Tomorrow", False)
    assert store.todo_tag_label({"tag": "on Tue", "date": iso(YESTERDAY)}, TODAY) == ("on Tue", True)
    assert store.todo_tag_label(
        {"tag": "on Tue", "date": iso(YESTERDAY), "done": True}, TODAY
    ) == ("on Tue", False)


# --- JSON I/O ---------------------------------------------------------------

def test_write_then_read_roundtrip(tmp_path):
    path = tmp_path / "nested" / "events.json"
    store.write_json_file(str(path), {"2026-01-01": [{"title": "café"}]}, ensure_ascii=False)
    assert store.read_json_file(str(path)) == {"2026-01-01": [{"title": "café"}]}
    assert not (tmp_path / "nested" / "events.json.tmp").exists()


def test_read_missing_or_corrupt_returns_default(tmp_path):
    assert store.read_json_file(str(tmp_path / "nope.json"), {"d": 1}) == {"d": 1}
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    assert store.read_json_file(str(bad), []) == []
    binary = tmp_path / "bin.json"
    binary.write_bytes(b"\xff\xfe\x00garbage")
    assert store.read_json_file(str(binary), []) == []


def test_safe_int():
    assert store.safe_int("7", 0) == 7
    assert store.safe_int(None, 3) == 3
    assert store.safe_int("x", 3) == 3


# --- paths ------------------------------------------------------------------

def test_data_dir_env_override(tmp_path):
    assert store.user_data_dir({"FOCI_DATA_DIR": str(tmp_path)}) == str(tmp_path)


def test_data_dir_from_source_is_assets(monkeypatch):
    monkeypatch.delattr("sys._MEIPASS", raising=False)
    monkeypatch.setattr("sys.frozen", False, raising=False)
    assert store.user_data_dir({}) == os.path.join(store.app_root(), "assets")


def test_frozen_build_never_writes_into_bundle(monkeypatch, tmp_path):
    # Regression: the one-file .exe saved user data inside its temp extraction
    # folder (sys._MEIPASS), which PyInstaller deletes when the app exits.
    bundle = tmp_path / "_MEI12345"
    monkeypatch.setattr("sys._MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr("sys.frozen", True, raising=False)
    data_dir = store.user_data_dir({"APPDATA": str(tmp_path / "Roaming")})
    assert store.app_root() == str(bundle)
    assert not data_dir.startswith(str(bundle))


@pytest.mark.parametrize(
    "platform, environ, expected_tail",
    [
        ("win32", {"APPDATA": "/r"}, os.path.join("/r", "Foci")),
        ("darwin", {}, os.path.join("Library", "Application Support", "Foci")),
        ("linux", {"XDG_DATA_HOME": "/x"}, os.path.join("/x", "Foci")),
        ("linux", {}, os.path.join(".local", "share", "Foci")),
    ],
)
def test_platform_data_dir(platform, environ, expected_tail):
    assert store.platform_data_dir(platform=platform, environ=environ).endswith(expected_tail)


def test_app_root_does_not_depend_on_cwd(monkeypatch, tmp_path):
    monkeypatch.delattr("sys._MEIPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    assert os.path.isfile(os.path.join(store.app_root(), "main.py"))
