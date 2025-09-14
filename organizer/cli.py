
from __future__ import annotations
import argparse
import logging
from pathlib import Path
from .core import Organizer, UndoManager

LOG = logging.getLogger("organizer")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="organizer",
        description="Organize files by extension, MIME type, or date.",
    )
    p.add_argument("path", nargs="?", default=".", help="Directory to organize (default: .)")
    p.add_argument("--by", choices=("ext", "mime", "date"), default="ext", help="Grouping strategy (default: ext)")
    p.add_argument("--date-field", choices=("mtime", "ctime"), default="mtime", help="Which timestamp to use when --by date (default: mtime)")
    p.add_argument("--dest", default=None, help="Destination base directory (default: <path>/organized)")
    p.add_argument("--copy", action="store_true", help="Copy files instead of moving")
    p.add_argument("--dry-run", action="store_true", help="Show what would happen; no changes made")
    p.add_argument("--manifest", default=None, help="Path to manifest file for recording or undoing moves")
    p.add_argument("--include", nargs="+", default=None, help="Glob patterns to include (e.g., *.jpg *.png)")
    p.add_argument("--exclude", nargs="+", default=None, help="Glob patterns to exclude (e.g., *.tmp)")
    p.add_argument("--max-depth", type=int, default=None, help="Recurse up to N levels (default: unlimited)")
    p.add_argument("--undo", action="store_true", help="Undo operations recorded in --manifest")
    p.add_argument("--verbose", action="store_true", help="More logs")
    return p

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    root = Path(args.path).expanduser().resolve()
    if args.dest:
        dest = Path(args.dest).expanduser().resolve()
    else:
        dest = root / "organized"

    if args.undo:
        if not args.manifest:
            LOG.error("--undo requires --manifest path to a manifest JSON file.")
            return 2
        um = UndoManager(Path(args.manifest))
        return um.undo(dry_run=args.dry_run)

    org = Organizer(
        root=root,
        dest=dest,
        by=args.by,
        date_field=args.date_field,
        copy=args.copy,
        include=args.include,
        exclude=args.exclude,
        max_depth=args.max_depth,
        manifest_path=Path(args.manifest) if args.manifest else None,
    )
    planned = org.plan()
    org.apply(planned, dry_run=args.dry_run)
    return 0
