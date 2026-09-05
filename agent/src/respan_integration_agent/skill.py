"""Ship and provision the reviewed Respan skill for each controller session."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import tempfile
from typing import Iterator

SOURCE_COMMIT = "4496befb9b3f61e95f0f26cee2a90c1465720ffd"
SOURCE_PATH = "claude-plugin/skills/respan"
FILES = {
    "SKILL.md": "362573c74407e81c9643443518ff00e09457302c279c9325c4461b5e8d1b1184",
    "references/evals.md": "891f67018af2e22a4d89d4779f4282a7c70f89c4670cb0ec4d79e5dd9dc43271",
    "references/gateway.md": "6bff261df498fc6e6f576b4191c7d5c3fc3d1ca002ff16e2f3838bbed504961a",
    "references/monitors.md": "a2aa9eba2b5c98ba6cec1b8d5d08f2c0192dbeebf6b1589bce1de9975697337e",
    "references/prompts.md": "073420d2d7aeff29b75f3508f99b4b8d191217a49b1d396649ba13e6b3ff4fbc",
    "references/tracing.md": "bdacdb74b0cf32f353da2534b8637c7b0cd1abbec62a3805a459278d08fd57b9",
}


def bundled_skill_dir() -> Path:
    return Path(__file__).resolve().parent / "resources" / "respan"


def validate_skill_source(source: Path | None = None) -> Path:
    selected = source or bundled_skill_dir()
    if selected.is_symlink() or not selected.is_dir():
        raise ValueError("The bundled Respan skill is missing or is not a real directory")
    actual = set()
    for path in selected.rglob("*"):
        if path.is_symlink():
            raise ValueError("The bundled Respan skill contains a symlink")
        if path.is_file():
            actual.add(path.relative_to(selected).as_posix())
    if actual != set(FILES):
        raise ValueError("The bundled Respan skill does not match the reviewed file inventory")
    for name, expected in FILES.items():
        if hashlib.sha256((selected / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Bundled Respan skill hash mismatch: {name}")
    return selected.resolve()


@dataclass(frozen=True)
class ProvisionedSkill:
    config_dir: Path
    skill_dir: Path

    def receipt(self) -> dict:
        return {"source_commit": SOURCE_COMMIT, "source_path": SOURCE_PATH,
                "files": dict(FILES), "isolated": True}


@contextmanager
def provision_respan_skill(source: Path | None = None) -> Iterator[ProvisionedSkill]:
    """Avoid ambient skills/settings and leave the user's Claude configuration alone."""
    selected = validate_skill_source(source)
    with tempfile.TemporaryDirectory(prefix="respan-agent-skill-") as temp:
        config_dir = Path(temp).resolve()
        (config_dir / "home" / ".config").mkdir(parents=True)
        skill_dir = config_dir / "skills" / "respan"
        shutil.copytree(selected, skill_dir)
        validate_skill_source(skill_dir)
        yield ProvisionedSkill(config_dir=config_dir, skill_dir=skill_dir)
