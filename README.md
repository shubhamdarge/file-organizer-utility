# File Organizer Utility (Python)

A practical automation script that organizes files into folders by **type** (extension / MIME) or **date** (created/modified).  
Includes a flexible CLI, dry-run mode, and an **undo** feature using a manifest file. Tested with `pytest`.

## Quick Start

```bash
# 1) Create a virtual environment (optional)
python3 -m venv .venv && source .venv/bin/activate

# 2) Install dev requirements (only pytest; the tool itself uses stdlib)
pip install -r requirements.txt

# 3) Run (examples)
python -m organizer --help
python -m organizer ~/Downloads --by ext --dry-run
python -m organizer ~/Downloads --by date --date-field mtime
python -m organizer ~/Downloads --by mime --dest ~/Downloads/organized --manifest moves.json
python -m organizer --undo --manifest moves.json
```

## What it does

- Groups files by **extension**, **MIME type**, or **date** (year/month/day).
- Moves (default) or copies files into an output directory.
- **Dry-run** to preview actions, **undo** to revert moves using a manifest.
- Include/exclude glob patterns, recursion depth, and safe overwrite behavior.

## CLI Usage

```text
usage: python -m organizer [-h] [path] [--by {ext,mime,date}] [--date-field {mtime,ctime}]
                           [--dest DEST] [--copy] [--dry-run] [--manifest MANIFEST]
                           [--include INCLUDE ...] [--exclude EXCLUDE ...]
                           [--max-depth MAX_DEPTH] [--undo] [--verbose]

positional arguments:
  path                  Directory to organize (default: .)

options:
  --by {ext,mime,date}  Grouping strategy (default: ext)
  --date-field {mtime,ctime}
                        Which timestamp to use when --by date (default: mtime)
  --dest DEST           Destination base directory (default: <path>/organized)
  --copy                Copy files instead of moving
  --dry-run             Show what would happen; no changes made
  --manifest MANIFEST   Path to manifest file for recording or undoing moves
  --include ...         One or more glob patterns to include (e.g., *.jpg *.png)
  --exclude ...         One or more glob patterns to exclude (e.g., *.tmp)
  --max-depth N         Recurse up to N levels (default: unlimited)
  --undo                Undo operations recorded in --manifest
  --verbose             More logs
```

## Project Structure

```
organizer/
  __init__.py
  __main__.py         # Enables `python -m organizer`
  cli.py              # argparse + logging
  core.py             # core logic (scan, plan, apply, undo)
tests/
  test_core.py
requirements.txt       # pytest for tests (stdlib for tool)
.gitignore
README.md
```

## Why this project?

- Shows **scripting & automation** skills.
- Clean, testable design with separation of concerns.
- No external dependencies (except `pytest` for tests).
