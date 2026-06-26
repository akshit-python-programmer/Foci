# Foci — Technical Deep Dive

[← Back to README](../README.md)

This document walks through the non-trivial engineering decisions behind Foci for anyone who wants to understand what was actually built, not just what it does.

---

## Architecture overview

Foci is a single-process desktop app with one deliberate exception: the lofi music player spawns as a separate `multiprocessing.Process` so audio never blocks the 60 fps render loop. Everything else — rendering, input, persistence, animations — runs on the main thread in a classic game-loop pattern.

```
main.py  (main process, 60 fps game loop)
│
├── utility.py          helper functions (math, color, font cache, drawing primitives)
├── google_calendar.py  optional OAuth2 calendar sync (self-contained)
├── progress.py         standalone focus-timer demo
│
└── subprocess: simple_music_player_process()
        └── SMTCController  WinRT media-key / tray integration
```

Data is stored in four plain JSON files in `assets/`. No database, no cloud, no framework.

---

## Immediate-mode GUI from scratch

There is no GUI toolkit. Every pixel is drawn manually using `pygame.draw.*` and `pygame.gfxdraw` each frame. This required implementing:

**Layout and hit-testing.** All interactive regions are `pygame.Rect` objects computed fresh each frame from the window dimensions. Clicks are tested against these rects in `MOUSEBUTTONDOWN` handlers. This means the UI is always in sync with window size — resize works for free.

**Scrolling with physics.** Both the timeline and the to-do list have inertia scrolling. A `scroll_velocity` accumulates from mouse-wheel events and decays each frame with a friction coefficient (`*= 0.90`). Clamping with an ease-back creates the "bounce" feel at the top/bottom of the scroll area. Clipping rectangles (`screen.set_clip()`) ensure off-screen content is never rendered.

**Drag-and-drop events.** `MOUSEBUTTONDOWN` records the drag origin and the event under the cursor. `MOUSEMOTION` updates a `temp_x` / `temp_y` on the event dict. On release, the new hour/minute is snapped by reverse-mapping the y-coordinate back through the grid formula:

```python
hour = START_HOUR + (y - TOP_Y + scroll_offset) / HOUR_HEIGHT
```

**Overlap layout.** When two events share a time slot, `calculate_event_layout()` groups them and assigns each a column using a greedy interval-scheduling pass, then divides the available width equally. This runs every frame so it handles drag-in-progress correctly.

---

## Rendering techniques

**Supersampled event cards.** Each event is rendered onto a surface 3× its display size, then `pygame.transform.smoothscale`'d down. This gives sub-pixel smooth rounded corners and gradients at no extra draw cost beyond the initial blit.

**Per-pixel day-arc gradient.** The timeline background shifts through a colour keyframe table (`DAY_ARC`) anchored to actual clock hours — dawn blues, midday whites, golden hour oranges, deep night purples. Each hour row is filled line-by-line with linear interpolation between adjacent keyframes. The result is a single RGBA surface blitted with `set_clip` so it scrolls with the grid.

**Animated wave gradient for theme backgrounds.** Several themes use `math.sin(pygame.time.get_ticks() / 5000 * π)` to slowly oscillate between two colours, creating a breathing background that never repeats.

**Glassmorphism quote toasts.** When a to-do is completed, a motivational quote appears. Its background is produced by subsurfacing the pixels behind the toast rect, scaling them down 8× and back up (a fast box blur), then blitting a semi-transparent overlay on top. This runs per-frame for the toast's slide-in duration.

**Confetti physics.** 80 particles are spawned per completion event, each with a random angle, speed, and colour. Each frame: velocity accumulates gravity (+0.4 y), air resistance damps x velocity (×0.98), particle size shrinks slightly. Particles are culled when their life counter hits zero.

---

## Multiprocessing music player

The lofi player is a fully independent pygame window running in a `daemon=True` subprocess. It communicates zero state back to the main process — it simply plays audio and handles its own events. This means:

- A crash in the player never crashes the calendar
- The player window can be closed and re-opened without affecting playback history in the main app
- The main app's 60 fps loop is never blocked by audio I/O

The player has three adaptive layouts (full / compact / micro) based on window dimensions, and supports dragging its frameless window via the native Win32 API (`ReleaseCapture` + `SendMessageW(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0)`) — cleaner than tracking mouse deltas.

---

## Windows SMTC integration

`SMTCController` wraps WinRT's `winrt.windows.media.playback.MediaPlayer` to register the app with Windows' System Media Transport Controls — the same mechanism Spotify and Chrome use to appear in the media flyout and respond to keyboard media keys.

The tricky parts:
- WinRT callbacks fire on a background thread, so a `queue.Queue` is used to marshal commands (`play`, `pause`, `next`, `prev`) back to the player's pygame loop safely.
- The `MediaPlayer`'s built-in command manager is disabled; we drive the `SystemMediaTransportControls` manually so pygame remains the sole audio controller.
- Thumbnail art is loaded by writing raw bytes into a WinRT `InMemoryRandomAccessStream` via `asyncio.run()` in a one-shot coroutine.

---

## Data model and local-first design

Events are keyed by date string (`"YYYY-MM-DD"`) in a single JSON dict. To-dos are a recursive tree of `{type, children}` nodes supporting arbitrary folder nesting. Both are loaded on startup and saved on every mutation.

Resilience strategy: every `json.load` call is wrapped in try/except; a malformed file silently falls back to an empty default rather than crashing. Example templates (`*.example.json`) are committed so new users see the expected shape immediately.

The `todo_id` field cross-links to-dos and events: checking off an event automatically marks the linked to-do as done (and vice versa), keeping both panels in sync without a shared state object.

---

## Packaging

`main.spec` is a hand-tuned PyInstaller spec that bundles all assets (fonts, icons, sounds, sprite sheets) into the executable using `datas`. `resource_path()` in `utility.py` resolves paths correctly whether running from source or from the PyInstaller `_MEIPASS` temp directory.

---

## Skills demonstrated

| Skill | Where |
|---|---|
| Python (OOP, closures, generators) | Throughout — event loop, recursive todo tree, font cache |
| Custom GUI architecture | Immediate-mode layout, hit-testing, clipping, scroll physics |
| Rendering / graphics | Supersampling, per-pixel gradients, particle systems, glassmorphism |
| Multiprocessing & IPC | Music player subprocess, thread-safe queue for SMTC callbacks |
| Windows native API | WinRT SMTC, Win32 window dragging via ctypes |
| OAuth2 / REST | Google Calendar sync (google-api-python-client) |
| UX / product thinking | ADHD-friendly design, gamification loops, calm reward patterns |
| Packaging & distribution | PyInstaller spec, resource path abstraction |
| Data design | Recursive JSON tree, cross-linked todo↔event, resilient loading |
