
from pathlib import Path
import json
import tempfile
from organizer.core import Organizer, UndoManager

def create_file(path: Path, size: int = 0):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        if size:
            f.write(b"\0" * size)
        else:
            f.write(b"x")

def test_plan_and_apply_by_ext(tmp_path: Path):
    # Arrange
    root = tmp_path / "inbox"
    create_file(root / "a.txt")
    create_file(root / "b.jpg")
    dest = tmp_path / "out"
    manifest = tmp_path / "moves.json"

    org = Organizer(root=root, dest=dest, by="ext", manifest_path=manifest)
    plan = org.plan()

    # Act
    org.apply(plan, dry_run=False)

    # Assert
    assert (dest / "txt" / "a.txt").exists()
    assert (dest / "jpg" / "b.jpg").exists()
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert len(data["operations"]) == 2

def test_dry_run(tmp_path: Path, capsys):
    root = tmp_path / "inbox"
    create_file(root / "c.md")
    dest = tmp_path / "out"

    org = Organizer(root=root, dest=dest, by="ext")
    plan = org.plan()
    org.apply(plan, dry_run=True)
    # Nothing should be created
    assert not (dest).exists()

def test_undo(tmp_path: Path):
    root = tmp_path / "inbox"
    create_file(root / "x.txt")
    dest = tmp_path / "out"
    manifest = tmp_path / "moves.json"

    org = Organizer(root=root, dest=dest, by="ext", manifest_path=manifest)
    plan = org.plan()
    org.apply(plan, dry_run=False)

    # File moved
    assert not (root / "x.txt").exists()
    assert (dest / "txt" / "x.txt").exists()

    um = UndoManager(manifest)
    um.undo(dry_run=False)

    # Back to original place
    assert (root / "x.txt").exists()
