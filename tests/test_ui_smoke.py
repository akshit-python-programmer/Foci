"""Render-level smoke tests: open real dialogs in a headless SDL window.

These catch crashes (NameError, UnboundLocalError, ...) in drawing code that
the unit tests in test_store.py can't reach.
"""
import os
import tempfile

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("FOCI_DATA_DIR", tempfile.mkdtemp(prefix="foci-test-"))

pygame = pytest.importorskip("pygame")
main = pytest.importorskip("main")


class _StopDialog(Exception):
    pass


@pytest.fixture
def stop_after_frames(monkeypatch):
    """Let a modal dialog draw ``n`` frames, then break out of its loop."""
    def install(n):
        state = {"frames": 0}
        real_flip = pygame.display.flip

        def flip():
            real_flip()
            state["frames"] += 1
            if state["frames"] >= n:
                raise _StopDialog
        monkeypatch.setattr(pygame.display, "flip", flip)
        return state
    return install


@pytest.mark.parametrize("edit", [False, True])
def test_event_dialog_renders(stop_after_frames, edit):
    # Regression: y_offset was never initialised, so opening the Add/Edit Event
    # dialog crashed the whole app with UnboundLocalError.
    main.load_settings()
    existing = {"title": "Gym", "hour": 9, "minute": 0, "duration": 60, "color": [1, 2, 3], "icon": 0}
    state = stop_after_frames(30)
    with pytest.raises(_StopDialog):
        main.event_add_window(pos=(10, 0), edit_event=existing if edit else None)
    assert state["frames"] == 30


def test_stats_popup_renders(stop_after_frames):
    stop_after_frames(5)
    with pytest.raises(_StopDialog):
        main.show_stats_popup(main.events, main.screen, main.font_cache,
                              main.settings.get("font_path"), main.WIDTH, main.HEIGHT)


# --- keyboard shortcuts -----------------------------------------------------

@pytest.fixture
def sample_todos(monkeypatch):
    todos = [
        {"type": "todo", "title": "a", "done": False},
        {"type": "folder", "name": "F", "is_open": True, "children": [
            {"type": "todo", "title": "f1", "done": False},
        ]},
    ]
    monkeypatch.setattr(main, "todos", todos)
    monkeypatch.setattr(main, "selected_todo_path", None)
    monkeypatch.setattr(main, "save_todos", lambda: None)
    monkeypatch.setattr(main, "trigger_motivational_quote", lambda *a, **k: None)
    return todos


def test_arrow_keys_walk_into_open_folders(sample_todos):
    for _ in range(3):
        assert main.handle_todo_shortcut(pygame.K_DOWN)
    assert main.selected_todo_path == (1, 0)
    main.handle_todo_shortcut(pygame.K_k)
    assert main.selected_todo_path == (1,)


def test_space_checks_off_nested_todo(sample_todos):
    main.selected_todo_path = (1, 0)
    assert main.handle_todo_shortcut(pygame.K_SPACE)
    assert sample_todos[1]["children"][0]["done"] is True


def test_space_on_folder_toggles_it(sample_todos):
    main.selected_todo_path = (1,)
    main.handle_todo_shortcut(pygame.K_RETURN)
    assert sample_todos[1]["is_open"] is False


def test_number_keys_schedule(sample_todos):
    main.selected_todo_path = (0,)
    main.handle_todo_shortcut(pygame.K_2)
    assert sample_todos[0]["tag"] == "tmr"
    main.handle_todo_shortcut(pygame.K_3)
    assert "tag" not in sample_todos[0]


def test_delete_key_removes_and_keeps_selection_valid(sample_todos):
    main.selected_todo_path = (1, 0)
    main.handle_todo_shortcut(pygame.K_DELETE)
    assert sample_todos[1]["children"] == []
    assert main.selected_todo_path == (1,)


def test_keys_without_selection_are_ignored(sample_todos):
    assert main.handle_todo_shortcut(pygame.K_SPACE) is False
    assert main.handle_todo_shortcut(pygame.K_1) is False
    assert main.handle_todo_shortcut(pygame.K_ESCAPE) is True


def test_selected_row_is_drawn(sample_todos, monkeypatch):
    main.selected_todo_path = (1, 0)
    main.draw_todo_list((-100, -100))  # must not raise


def test_shortcuts_help_closes_on_key(monkeypatch):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode="a", mod=0, scancode=0))
    main.show_shortcuts_help()  # returns instead of looping forever


# --- themes -----------------------------------------------------------------

REQUIRED_THEME_KEYS = {
    "background", "text", "event_done_color", "event_dimmed", "hour_line",
    "title_color", "progress_bar", "current_event_dim", "settings_bg",
    "todo_bg", "todo_item_bg", "todo_item_hover", "button_bg", "color_choices",
}


@pytest.mark.parametrize("name", list(main.THEMES))
def test_every_theme_is_complete_and_renders(name, monkeypatch):
    theme = main.THEMES[name]
    assert REQUIRED_THEME_KEYS <= theme.keys(), REQUIRED_THEME_KEYS - theme.keys()
    if theme.get("use_gradient_bg"):
        assert {"gradient_start", "gradient_end"} <= theme.keys()
    assert len(theme["color_choices"]) == 5
    monkeypatch.setattr(main, "THEME", theme)
    monkeypatch.setattr(main, "current_theme", name)
    layout = main.calculate_event_layout(main.events, main.WIDTH - main.EVENT_X - main.EVENT_RIGHT_MARGIN)
    main.draw_day_view(layout)
    main.draw_todo_list((-1, -1))
