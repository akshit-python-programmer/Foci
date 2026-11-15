# Changelog

All notable changes to Foci are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- **Opening the Add/Edit Event dialog crashed the app** (`UnboundLocalError: y_offset`).
- Pressing <kbd>S</kbd> for stats crashed the app (`NameError: font_path`).
- **Packaged app lost all data on restart.** The one-file `.exe` wrote events, to-dos, settings and coins into PyInstaller's temporary extraction folder, which is deleted on exit. User data now lives in the OS app-data folder for packaged builds (`%APPDATA%\Foci` etc.) and stays in `assets/` when running from source.
- Launching `python path/to/main.py` from a different directory couldn't find fonts, icons or the coin sprite sheet. Resources now resolve relative to the app, not the working directory.
- "Schedule for Tomorrow" set the `tmr` tag and then immediately deleted it.
- Date tags didn't roll over for to-dos inside folders.
- "Delete completed" ignored completed to-dos inside folders.
- Google Calendar: fixed an import that always failed (`google.auth_oauthlib` → `google_auth_oauthlib`), the day window being computed in UTC instead of local time, event times not being converted to local time, and all-day events being imported as 24-hour blocks.
- `format_time` wrapped around for durations of 24 hours or more.
- An unreadable data file (e.g. wrong text encoding) no longer crashes startup.
- Packaged builds call `multiprocessing.freeze_support()` so the lofi player subprocess starts correctly.

### Added
- **Keyboard shortcuts** for to-dos (select, check off, schedule, add, delete) and calendar navigation, plus a <kbd>?</kbd> help overlay. Suggested by Fazal.
- **Three new themes**: Ocean Breeze, Lavender Dusk and Matcha Latte. Suggested by Anaconda bro.
- To-dos show a date pill (*Today*, *Tomorrow*, *on Mon*), red when overdue.
- `FOCI_DATA_DIR` environment variable to choose where data is stored.
- `foci_store.py`: persistence and validation split out of `main.py` so it can be tested.
- Test suite (`pytest`) and GitHub Actions CI on Windows, macOS and Linux.
- Contributor guide, issue templates and pull request template.

### Changed
- The built executable is named `Foci.exe` instead of `main.exe`.
- The <kbd>T</kbd> theme shortcut now remembers the chosen theme.

## [1.0.0] - initial release

- Day timeline with drag-to-create, move and resize events
- Nested to-do list with folders
- Focus timer, lofi music player with Windows media-key integration
- 8 themes, font picker, confetti, coin rewards, stats and weekly view
- Local-first JSON storage, PyInstaller build
