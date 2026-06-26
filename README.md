# Foci — a calm, ADHD-friendly focus calendar

> A day-planner, to-do list, and focus timer in one quiet window. Built to make starting the day feel manageable instead of overwhelming.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![pygame](https://img.shields.io/badge/Built%20with-pygame-44cc11)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

Foci is a desktop planner I built for myself because most productivity apps felt loud and punishing. It puts a visual hourly timeline, a nested to-do list, and a focus timer side by side, with calm themes, optional lofi, and small rewards for finishing things — inspired by tools like Tiimo and Llama Life.

## Demo

<!-- Replace with a real screenshot / GIF: drop an image at docs/demo.png and update this line -->
![Foci screenshot](docs/demo.png)

*(Screenshot / GIF placeholder — record a short clip of dragging an event onto the timeline and a task being checked off.)*

## Features

- **Visual day timeline** — drag on the calendar to create events, then drag to move or resize them across an hourly grid. Configurable day start/end hours and zoom (hour height).
- **Nested to-do list** — organize tasks into collapsible folders (e.g. Physics → Kinematics → today's set), with date tags like *today* / *tomorrow* that roll forward automatically.
- **Focus timer** — a smooth circular countdown timer for working in focused blocks (`progress.py` is a standalone visual demo of the timer).
- **8 calm themes** — Serene Morning, Golden Hour, Midnight Deep, Cyberpunk Night, Forest Canopy, Classic Light, Classic Dark, and Kyoto Spring, several with gradient backgrounds.
- **Gentle gamification** — earn coins and a confetti burst when you complete tasks, with an animated coin sprite, to make finishing feel good rather than guilt-driven.
- **Lofi music player** — built-in lofi tracks you can toggle on/off while you work.
- **Weekly view & sound** — a weekly overview and soft completion sounds.
- **Optional Google Calendar sync** — `google_calendar.py` provides a self-contained OAuth flow to sync with Google Calendar (bring your own `credentials.json`; see below).
- **Local-first** — all your tasks, events, and settings live in plain JSON files on your machine. Nothing is uploaded.

## Tech stack

- **Python 3.10+**
- **[pygame](https://www.pygame.org/)** — rendering, input, audio mixer
- A hand-built **immediate-mode UI** drawn with `pygame.gfxdraw` (custom buttons, drag/resize hit-testing, animations) — no GUI toolkit
- **JSON** for local persistence
- *(optional)* **google-api-python-client / google-auth-oauthlib** for calendar sync

## Install & run

```bash
# 1. Clone
git clone https://github.com/akshitkumarlall/foci.git
cd foci

# 2. (recommended) create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

To try just the focus timer demo:

```bash
python progress.py
```

## Optional: Google Calendar sync

`google_calendar.py` is an optional module. To use it:

1. In the [Google Cloud Console](https://console.cloud.google.com/), create an OAuth 2.0 Desktop client and enable the Google Calendar API.
2. Download the client secret as `credentials.json` and place it in the `assets/` folder.
3. On first run the module opens a browser to authorize; it then stores a `token.json` locally.

`credentials.json` and `token.json` are git-ignored and must never be committed.

## Your data

Foci stores everything locally in `assets/`:

| File | What it holds |
|------|---------------|
| `settings.json` | theme, day hours, zoom, sound/confetti toggles |
| `todos.json` | your to-do list and folders |
| `events.json` | scheduled calendar events |
| `player_data.json` | coin count |

These are git-ignored so your personal schedule stays private. Sample `*.example.json` files are included to show the format — copy one and drop the `.example` to start from a template, or just run the app and it will create fresh files for you.

## What I learned

- Designing **calm, focus-supporting UX** — color, pacing, and reward loops that reduce friction instead of adding pressure.
- Building a **custom immediate-mode GUI from scratch in pygame**: layout, hit-testing, and drag-to-resize/move interactions without a UI framework.
- **Sprite-sheet animation** and lightweight visual effects (gradients, confetti, eased transitions).
- **Local-first persistence** with JSON and resilient loading (graceful defaults when files are missing or malformed).
- Packaging a Python app into a standalone Windows executable with PyInstaller (`main.spec`).

## Building a standalone executable (optional)

```bash
pip install pyinstaller
pyinstaller main.spec
# output in dist/
```

## License

MIT — see [LICENSE](LICENSE).

Bundled third-party assets (UI sprite packs under `assets/`, the Domine font, lofi tracks) retain their own licenses; see the license/readme files included in those subfolders.
