# Foci — calm, ADHD-friendly focus calendar

> A day-planner, to-do list, and focus timer in one quiet window. Built to make starting the day feel manageable instead of overwhelming.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![pygame](https://img.shields.io/badge/Built%20with-pygame-44cc11)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

<div align="center">
  <a href="docs/TECHNICAL.md">
    <img src="https://img.shields.io/badge/%F0%9F%94%A7%20Technical%20Deep%20Dive-How%20It%20Was%20Built-6e40c9?style=for-the-badge" alt="Technical Report"/>
  </a>
</div>

---

Foci is a desktop planner I built for myself because most productivity apps felt loud and punishing. It puts a visual hourly timeline, a nested to-do list, and a focus timer side by side — with calm themes, optional lofi music, and small rewards for finishing things. Inspired by tools like Tiimo and Llama Life, but built from scratch with no UI framework.

## Screenshot

![Foci main view](demo/example%20of%20how%20it%20looks%20like%20.png)

## Demo clips

<table>
  <tr>
    <td align="center"><b>Calendar & events</b></td>
    <td align="center"><b>Focus timer</b></td>
    <td align="center"><b>Task check-off + lofi player</b></td>
  </tr>
  <tr>
    <td>

https://github.com/user-attachments/assets/calendar-view

> [`demo/calendar view.mp4`](demo/calendar%20view.mp4)
    </td>
    <td>

> [`demo/focus timer feature.mp4`](demo/focus%20timer%20feature.mp4)
    </td>
    <td>

> [`demo/task check off + lofi music player.mp4`](demo/task%20check%20off%20%20%2B%20lofi%20music%20player.mp4)
    </td>
  </tr>
  <tr>
    <td align="center"><b>Theme switcher</b></td>
    <td align="center"><b>Full walkthrough</b></td>
    <td></td>
  </tr>
  <tr>
    <td>

> [`demo/different themes.mp4`](demo/different%20themes.mp4)
    </td>
    <td>

> [`demo/small demo.mp4`](demo/small%20demo.mp4)
    </td>
    <td></td>
  </tr>
</table>

> **Note:** GitHub renders `.mp4` files natively when you open the link. Click any filename above to watch in-browser.

---

## Features

### Day timeline
- Drag on the hourly grid to create events; drag events to move them, drag the bottom edge to resize
- Overlapping events auto-layout into side-by-side columns
- Animated red "current time" line with a pulsing comet head scrolls through your day
- Per-hour background shifts from dawn tints → midday → golden hour → night based on actual clock time
- Day progress bar at the bottom fills as the day goes on

### Event editor
- Modal dialog with animated slide-in
- Date picker (navigate days), time picker (hour/minute in 15-min steps), duration slider
- Color picker (5 theme-matched swatches) and icon picker (30 Lucide SVG icons: brain, atom, code, rocket, trophy, and more)
- Edit or delete existing events; editing can move an event to a different date

### Nested to-do list
- Flat tasks and collapsible folders (e.g. Physics → Kinematics → today's problems)
- Date tags: *today*, *tomorrow*, *someday* — tags roll forward automatically at midnight
- Drag-and-drop reordering within the list
- Right-click context menu to schedule a task (Today / Tomorrow / Someday)
- Delete completed tasks in bulk with one button

### Focus timer
- Click the ▶ button on any currently-active event to open a standalone focus timer popup
- Large MM:SS countdown with a green progress bar; Space or the button to play/pause
- Separate circular progress arc in the sidebar tracks the current event in real time with a rotating "bean" knob

### Lofi music player
- Launches as a separate frameless subprocess window (doesn't block the main app)
- Playlist view, play/pause/prev/next/shuffle, volume and seek scrubbing
- Three adaptive layouts: full (playlist visible), compact, and micro (controls only)
- Draggable titlebar via native Win32 `ReleaseCapture` / `SendMessage`
- **Windows SMTC integration** — registers with the system media flyout so track name appears in the tray and media keys (⏯ ⏭ ⏮) work system-wide

### Themes & fonts
- 8 built-in themes: **Serene Morning**, **Golden Hour**, **Midnight Deep**, **Cyberpunk Night**, **Forest Canopy**, **Classic Light**, **Classic Dark**, **Kyoto Spring**
- Several themes feature animated slow-wave gradient backgrounds
- Font picker scans `assets/` for any `.ttf` / `.otf` and previews them live (ships with Domine, Roboto, Arimo, SansCode, RobotoCondensed)

### Gamification & feedback
- Earn coins when you complete an event (1 coin per 5 min of duration); lose them if you uncheck
- Animated coin sprite on each event card shows coins at stake
- Confetti particle burst (80 particles, physics-based) on event completion
- Motivational quote toasts with glassmorphism blur and slide-in animation on to-do completion
- Ding sound effect on check-off

### Stats
- Animated donut charts (ease-out cubic) showing tasks completed % and time focused % for the day

### Weekly view
- 7-column overview with event cards per day; click a day to jump to it; today column is highlighted

### Settings panel
- Scrollable modal: theme picker (shows each theme's actual colors as a preview), font picker, day start/end hour sliders, calendar zoom slider (30–80 px/hr), sound effects toggle, confetti toggle, lofi toggle

### Local-first & privacy
- All data lives in plain JSON files in `assets/`: `events.json`, `todos.json`, `settings.json`, `player_data.json`
- Personal files are git-ignored; `*.example.json` templates are included
- Nothing is uploaded anywhere

### Optional: Google Calendar sync
- `google_calendar.py` — standalone OAuth2 flow using `google-api-python-client`
- Bring your own `credentials.json` from Google Cloud Console; token is stored locally and never committed

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.10+ |
| Rendering & input | pygame 2 + `pygame.gfxdraw` |
| UI paradigm | Hand-built immediate-mode GUI (no framework) |
| Audio | `pygame.mixer` (mp3/wav playback, fade, seek) |
| System media keys | WinRT `winrt.windows.media` (SMTC) |
| Persistence | JSON (local flat files) |
| Packaging | PyInstaller (`main.spec`) → standalone `.exe` |
| Calendar sync (optional) | `google-api-python-client` + `google-auth-oauthlib` |

---

## Install & run

```bash
# 1. Clone
git clone https://github.com/akshitkumarlall/foci.git
cd foci

# 2. Create a virtual environment (recommended)
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

To try just the standalone focus timer:

```bash
python progress.py
```

---

## Optional: Google Calendar sync

1. In [Google Cloud Console](https://console.cloud.google.com/), create an OAuth 2.0 Desktop client and enable the Calendar API.
2. Download `credentials.json` → place in `assets/`.
3. First run opens a browser to authorize; token stored locally as `assets/token.json`.

Both files are git-ignored and must never be committed.

---

## Build a standalone .exe

```bash
pip install pyinstaller
pyinstaller main.spec
# output in dist/
```

---

## Your data

| File | Contents |
|---|---|
| `assets/settings.json` | Theme, day hours, zoom, toggles |
| `assets/todos.json` | To-do list and folder tree |
| `assets/events.json` | Scheduled calendar events |
| `assets/player_data.json` | Coin count |

These are git-ignored. Copy an `*.example.json` to get started, or just run the app — it creates fresh files automatically.

---

## What I learned

- Designing **calm, focus-supporting UX** — color palettes, pacing, and reward loops that reduce friction rather than adding pressure
- Building a **custom immediate-mode GUI from scratch in pygame**: layout, clipping, scrolling with physics, drag-and-drop hit-testing, and resize interactions with no framework
- **Multiprocessing** — the lofi player runs as a separate `multiprocessing.Process` so it never blocks the main event loop
- **WinRT / Windows SMTC integration** — registering a Python app with the system media transport controls so it behaves like a real media player
- **Sprite-sheet animation**, smooth gradients, per-pixel alpha overlays, and glassmorphism effects in pygame
- **Local-first data design** with resilient JSON loading (graceful defaults, malformed-file recovery)
- Packaging a Python app as a standalone Windows executable with PyInstaller

---

## License

MIT — see [LICENSE](LICENSE).

Bundled third-party assets (Domine font, Lucide icons under ISC, lofi tracks) retain their own licenses; see the license/readme files in their subfolders.
