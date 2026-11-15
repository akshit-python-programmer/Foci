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
