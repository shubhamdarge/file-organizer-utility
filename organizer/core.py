
from __future__ import annotations
import json
import logging
import mimetypes
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

LOG = logging.getLogger("organizer")

@dataclass(frozen=True)
class Move:
    src: Path
    dest: Path

class Organizer:
    def __init__(
        self,
        root: Path,
        dest: Path,
        by: str = "ext",
        date_field: str = "mtime",
        copy: bool = False,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        max_depth: int | None = None,
        manifest_path: Path | None = None,
    ):
        self.root = root
        self.dest = dest
        self.by = by
        self.date_field = date_field
        self.copy = copy
        self.include = include
        self.exclude = exclude
        self.max_depth = max_depth
        self.manifest_path = manifest_path

    def _iter_files(self) -> Iterator[Path]:
        """Yield files under root respecting max_depth, include/exclude globs."""
        if not self.root.exists():
            raise FileNotFoundError(self.root)

        root_depth = len(self.root.parts)
        for p in self.root.rglob("*"):
            if p.is_dir():
                # depth check on directories to avoid descending too far
                if self.max_depth is not None and len(p.parts) - root_depth > self.max_depth:
                    # Skip traversing deeper by clearing dirnames—rglob doesn't expose that, so rely on files depth check
                    continue
                continue
            if not p.is_file():
                continue
            # Depth check for files
            if self.max_depth is not None and len(p.parts) - root_depth > self.max_depth:
                continue
            rel = p.relative_to(self.root)

            # Exclude files inside the destination already
            if str(self.dest) in str(p.parent.resolve()):
                continue

            if self.include and not any(rel.match(pat) for pat in self.include):
                continue
            if self.exclude and any(rel.match(pat) for pat in self.exclude):
                continue
            yield p

    def _group_dir_for(self, file: Path) -> Path:
        if self.by == "ext":
            ext = file.suffix.lower().lstrip(".") or "no-ext"
            group = ext
        elif self.by == "mime":
            mt, _ = mimetypes.guess_type(file.name)
            if mt is None:
                group = "unknown"
            else:
                primary = mt.split("/")[0]
                group = f"{primary}"
        elif self.by == "date":
            stat = file.stat()
            ts = stat.st_mtime if self.date_field == "mtime" else stat.st_ctime
            dt = datetime.fromtimestamp(ts)
            group = f"{dt.year}/{dt.month:02d}/{dt.day:02d}"
        else:
            raise ValueError(f"Unknown grouping: {self.by}")
        return self.dest / group

    def plan(self) -> list[Move]:
        """Compute planned moves without touching filesystem."""
        moves: list[Move] = []
        for f in self._iter_files():
            target_dir = self._group_dir_for(f)
            # Keep original filename; disambiguate if needed during apply()
            moves.append(Move(src=f, dest=target_dir / f.name))
        LOG.info("Planned %d operations.", len(moves))
        return moves

    def apply(self, moves: list[Move], dry_run: bool = False) -> None:
        """Execute planned moves (or copy) with safe overwrite and optional manifest."""
        if dry_run:
            for m in moves:
                LOG.info("%s %s -> %s", "COPY" if self.copy else "MOVE", m.src, m.dest)
            LOG.info("Dry-run complete. No changes made.")
            return

        applied: list[tuple[str, str]] = []
        for m in moves:
            target_dir = m.dest.parent
            target_dir.mkdir(parents=True, exist_ok=True)

            final_dest = m.dest
            # Disambiguate if file exists
            counter = 1
            while final_dest.exists():
                stem = m.dest.stem
                suffix = m.dest.suffix
                final_dest = target_dir / f"{stem} ({counter}){suffix}"
                counter += 1

            if self.copy:
                shutil.copy2(m.src, final_dest)
            else:
                shutil.move(m.src, final_dest)

            applied.append((str(m.src), str(final_dest)))
            LOG.debug("%s %s -> %s", "COPIED" if self.copy else "MOVED", m.src, final_dest)

        if self.manifest_path:
            manifest = {
                "version": 1,
                "copy": self.copy,
                "by": self.by,
                "date_field": self.date_field,
                "root": str(self.root),
                "dest": str(self.dest),
                "operations": [{"src": s, "dest": d} for s, d in applied],
            }
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with self.manifest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            LOG.info("Wrote manifest with %d operations to %s", len(applied), self.manifest_path)

class UndoManager:
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path

    def load(self) -> dict:
        with self.manifest_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def undo(self, dry_run: bool = False) -> int:
        data = self.load()
        ops = data.get("operations", [])
        # Reverse order to move deepest last moved files first
        for op in reversed(ops):
            src = Path(op["dest"])
            dest = Path(op["src"])
            if dry_run:
                LOG.info("UNDO move %s -> %s", src, dest)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dest)
            LOG.debug("UNDID move %s -> %s", src, dest)
        LOG.info("Undo complete for %d operations.", len(ops))
        return 0
