# Contributing to Foci

Thanks for your interest! Foci is a small, calm desktop planner, and contributions of any size are welcome: bug reports, typo fixes, new themes, or bigger features.

## Getting set up

```bash
git clone https://github.com/akshit-python-programmer/Foci.git
cd Foci
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt pytest ruff
python main.py
```

While you're developing, you can keep your real planner data out of the way by pointing Foci at a scratch folder:

```bash
FOCI_DATA_DIR=/tmp/foci-dev python main.py
```

## Before you open a pull request

```bash
ruff check .
pytest -q
```

CI runs both on Windows, macOS and Linux, and also checks that `main.py` starts in a headless window.

## Project layout

| File | What's in it |
|---|---|
| `main.py` | The app: theme table, game loop, all drawing and input handling |
| `foci_store.py` | Loading, saving and validating settings / events / to-dos. No pygame, fully unit-tested. **Put new data logic here.** |
| `utility.py` | Drawing and math helpers shared by the UI |
| `google_calendar.py` | Experimental Google Calendar sync |
| `progress.py` | Standalone focus-timer demo |
| `tests/` | pytest suite |
| `assets/` | Fonts, icons, music, and `*.example.json` data templates |

`main.py` opens a window as soon as it's imported, so it can't be unit-tested directly. If you're adding logic that doesn't need to draw anything (date math, data cleanup, sorting), put it in `foci_store.py` with a test and call it from `main.py`.

## Guidelines

- **Keep it calm.** Foci is meant for people who find most productivity apps overwhelming. New UI should be quiet: soft colours, gentle animation, nothing that nags or punishes.
- **Don't break people's data.** Anything that changes the JSON format must still load old files. `foci_store.sanitize_*` is where to add defaults for new fields.
- **Small PRs are easier to review.** One fix or feature per PR, with a short description of what changed and how you tested it.
- **Include a screenshot or GIF** for visual changes.
- For bugs, add a regression test in `tests/` when you can.

## Reporting bugs

Please open an issue using the bug report template and include your OS, Python version, and steps to reproduce. If the bug involves your data, attach a trimmed copy of the relevant JSON file (remove anything personal).

## Licence

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
