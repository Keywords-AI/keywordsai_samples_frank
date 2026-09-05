"""Trusted lock-tool preflight and finalization, outside the model's Bash tool."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import tomllib
from typing import Any

PINNED_TOOLS = {"poetry": "2.4.2", "uv": "0.12.5"}
_SKIP_DIRECTORIES = {".git", ".venv", "venv", "node_modules", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache"}


class ToolchainError(RuntimeError):
    """A typed setup/lock failure; generated edits must remain available for review."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class LockProject:
    manager: str
    directory: str  # repository-relative, '.' for the root
    manifest_sha256: str
    lock_sha256: str | None


@dataclass(frozen=True)
class ToolchainReceipt:
    repository: str
    projects: tuple[LockProject, ...]
    executables: dict[str, str]
    versions: dict[str, str]
    executable_sha256: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def credential_free_environment(state_dir: Path, tool_bin: Path | None = None) -> dict[str, str]:
    """Allow only basic process settings; never forward model, registry, or Git credentials."""
    env = {key: os.environ[key] for key in ("LANG", "LC_ALL", "SYSTEMROOT", "WINDIR", "TMPDIR", "TMP", "TEMP") if key in os.environ}
    isolated_home = state_dir / "home"
    isolated_home.mkdir(parents=True, exist_ok=True)
    env.update({
        "HOME": str(isolated_home),
        "NETRC": os.devnull,
        "PATH": os.pathsep.join(filter(None, (str(tool_bin) if tool_bin else "", os.defpath))),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_SSH_COMMAND": "ssh -F /dev/null -o BatchMode=yes -o IdentitiesOnly=yes -o IdentityFile=/dev/null",
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "POETRY_CONFIG_DIR": str(state_dir / "poetry-config"),
        "POETRY_DATA_DIR": str(state_dir / "poetry-data"),
        "POETRY_CACHE_DIR": str(state_dir / "poetry-cache"),
        "POETRY_VIRTUALENVS_CREATE": "false",
        "POETRY_KEYRING_ENABLED": "false",
        "UV_CACHE_DIR": str(state_dir / "uv-cache"),
        "UV_PYTHON_DOWNLOADS": "never",
        "UV_PYTHON": sys.executable,
        "UV_KEYRING_PROVIDER": "disabled",
        "XDG_CONFIG_HOME": str(state_dir / "config"),
    })
    return env


def _safe_failure(output: str) -> str:
    # Public-index errors are useful (e.g. incompatible dependency constraints),
    # but redact credentials embedded in a declared repository URL or token field.
    output = re.sub(r"(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", output)
    output = re.sub(r"(?i)((?:api[_-]?key|token|password|authorization)\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]", output)
    return output[-2400:].strip()


def _run(argv: list[str], *, cwd: Path, env: dict[str, str], timeout_seconds: float, code: str) -> str:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Tool timeout must be finite and positive")
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    except OSError as exc:
        raise ToolchainError(code, f"Cannot start {Path(argv[0]).name}: {exc.strerror}") from exc
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except BaseException as exc:
        # Every command owns a process group, including metadata/build children.
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.communicate()
        if isinstance(exc, subprocess.TimeoutExpired):
            raise ToolchainError(code, f"{Path(argv[0]).name} exceeded its {timeout_seconds:g}s hang guard") from exc
        raise
    if process.returncode:
        raise ToolchainError(code, _safe_failure(stderr or stdout) or f"Tool exited {process.returncode}")
    return stdout.strip()


def discover_lock_projects(repository: Path) -> tuple[LockProject, ...]:
    repository = repository.resolve(strict=True)
    projects = []
    for current, directories, files in os.walk(repository, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in _SKIP_DIRECTORIES and not (Path(current) / name).is_symlink())
        if "pyproject.toml" not in files:
            continue
        directory = Path(current)
        manifest = directory / "pyproject.toml"
        if manifest.is_symlink():
            raise ToolchainError("TOOLCHAIN_MANIFEST_INVALID", "Lock manifests must be regular files inside the checkout")
        try:
            data = tomllib.loads(manifest.read_text())
        except (OSError, ValueError) as exc:
            raise ToolchainError("TOOLCHAIN_MANIFEST_INVALID", str(manifest.relative_to(repository))) from exc
        tool = data.get("tool", {})
        managers = []
        if (directory / "poetry.lock").exists() or "poetry" in tool:
            managers.append("poetry")
        if (directory / "uv.lock").exists() or "uv" in tool:
            managers.append("uv")
        for manager in managers:
            lock = directory / (manager + ".lock")
            if lock.is_symlink():
                raise ToolchainError("TOOLCHAIN_MANIFEST_INVALID", "Lockfiles must not be symlinks")
            projects.append(LockProject(manager, directory.relative_to(repository).as_posix(), _sha256(manifest), _sha256(lock)))
    return tuple(projects)


def preflight_toolchain(repository: Path, *, tool_bin: Path | None = None) -> ToolchainReceipt:
    """Discover required managers and verify their exact versions before a model call."""
    repository = repository.resolve(strict=True)
    projects = discover_lock_projects(repository)
    configured = tool_bin or (Path(os.environ["RESPAN_TOOLCHAIN_BIN"]) if os.environ.get("RESPAN_TOOLCHAIN_BIN") else None)
    configured = configured.expanduser().resolve() if configured else None
    executables = {}
    versions = {}
    executable_hashes = {}
    with tempfile.TemporaryDirectory(prefix="respan-tool-preflight-") as state:
        for manager in sorted({project.manager for project in projects}):
            selected = configured / manager if configured else shutil.which(manager)
            if not selected or not Path(selected).is_file() or not os.access(selected, os.X_OK):
                raise ToolchainError("TOOLCHAIN_MISSING", f"Install pinned {manager}=={PINNED_TOOLS[manager]} with `respan-integration-agent setup --toolchain-dir <new-directory>`, then set RESPAN_TOOLCHAIN_BIN to the reported tool_bin")
            executable = Path(selected).absolute()
            version_output = _run([str(executable), "--version"], cwd=Path(state), env=credential_free_environment(Path(state), executable.parent), timeout_seconds=15, code="TOOLCHAIN_VERSION_FAILED")
            match = re.search(r"\b(\d+\.\d+\.\d+)\b", version_output)
            actual = match.group(1) if match else None
            if actual != PINNED_TOOLS[manager]:
                raise ToolchainError("TOOLCHAIN_VERSION_MISMATCH", f"{manager} requires {PINNED_TOOLS[manager]}; found {actual or 'unrecognized version'}")
            executables[manager] = str(executable)
            versions[manager] = actual
            executable_hashes[manager] = _sha256(executable)
    return ToolchainReceipt(str(repository), projects, executables, versions, executable_hashes)


def finalize_lockfiles(repository: Path, receipt: ToolchainReceipt, *, timeout_seconds: float = 180) -> list[dict[str, Any]]:
    """Regenerate and check changed manifests' locks using exact trusted command arrays.

    This runs in the runner after editing, not through model Bash approvals. It does
    not install the target application, run it, or alter permission policies.
    """
    repository = repository.resolve(strict=True)
    if str(repository) != receipt.repository:
        raise ToolchainError("TOOLCHAIN_RECEIPT_MISMATCH", "Preflight receipt belongs to another checkout")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Lock tool timeout must be finite and positive")
    before = {(p.directory, p.manager): p for p in receipt.projects}
    after = {(p.directory, p.manager): p for p in discover_lock_projects(repository)}
    for key, previous in before.items():
        if key not in after:
            directory = repository / previous.directory
            manifest_hash = _sha256(directory / "pyproject.toml")
            if manifest_hash is None:
                raise ToolchainError("TOOLCHAIN_MANIFEST_REMOVED", previous.directory)
            after[key] = LockProject(previous.manager, previous.directory, manifest_hash, _sha256(directory / (previous.manager + ".lock")))
    results = []
    for project in after.values():
        previous = before.get((project.directory, project.manager))
        if previous == project:
            continue
        if project.manager not in receipt.executables:
            raise ToolchainError("TOOLCHAIN_NOT_PREFLIGHTED", f"New {project.manager} project requires setup before another model run")
        directory = (repository / project.directory).resolve(strict=True)
        if not directory.is_relative_to(repository):
            raise ToolchainError("TOOLCHAIN_RECEIPT_MISMATCH", "Project directory escaped its checkout")
        executable = receipt.executables[project.manager]
        if _sha256(Path(executable)) != receipt.executable_sha256.get(project.manager):
            raise ToolchainError("TOOLCHAIN_EXECUTABLE_CHANGED", project.manager)
        manifest = directory / "pyproject.toml"
        lock = directory / (project.manager + ".lock")
        manifest_hash = _sha256(manifest)
        if project.manager == "poetry":
            commands = [[executable, "--no-plugins", "--no-interaction", "lock"], [executable, "--no-plugins", "--no-interaction", "check", "--lock"]]
        else:
            commands = [[executable, "lock", "--no-python-downloads"], [executable, "lock", "--check", "--no-python-downloads"]]
        with tempfile.TemporaryDirectory(prefix="respan-lock-state-") as state:
            env = credential_free_environment(Path(state), Path(executable).parent)
            for argv in commands:
                _run(argv, cwd=directory, env=env, timeout_seconds=timeout_seconds, code="LOCK_FINALIZATION_FAILED")
        if _sha256(manifest) != manifest_hash:
            raise ToolchainError("LOCK_FINALIZATION_MUTATED_MANIFEST", project.directory)
        if not lock.is_file() or lock.is_symlink():
            raise ToolchainError("LOCK_FINALIZATION_FAILED", "Tool did not produce a regular lockfile")
        results.append({"manager": project.manager, "directory": project.directory, "version": receipt.versions[project.manager], "manifest_sha256": manifest_hash, "lock_sha256": _sha256(lock), "checked": True})
    return results


def bootstrap_toolchain(prefix: Path) -> dict[str, Any]:
    """Install the packaged, hash-locked tools into a fresh explicit virtualenv."""
    if not ((3, 11) <= sys.version_info[:2] < (3, 14)):
        raise ToolchainError("TOOLCHAIN_PYTHON_UNSUPPORTED", "Use Python >=3.11,<3.14 for the toolchain")
    prefix = prefix.expanduser().absolute()
    if prefix.exists():
        raise ToolchainError("TOOLCHAIN_PREFIX_EXISTS", "Choose a fresh isolated prefix; existing environments are preserved")
    lock = Path(__file__).resolve().parent / "resources/toolchain/requirements.lock"
    if not lock.is_file():
        raise ToolchainError("TOOLCHAIN_LOCK_MISSING", "The installed package is missing its toolchain requirements.lock")
    prefix.mkdir(parents=True, exist_ok=False)
    try:
        with tempfile.TemporaryDirectory(prefix="respan-tool-bootstrap-") as state:
            env = credential_free_environment(Path(state))
            _run([sys.executable, "-I", "-m", "venv", str(prefix)], cwd=Path(state), env=env, timeout_seconds=120, code="TOOLCHAIN_BOOTSTRAP_FAILED")
            bin_dir = prefix / ("Scripts" if os.name == "nt" else "bin")
            python = bin_dir / ("python.exe" if os.name == "nt" else "python")
            _run([str(python), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "install", "--timeout", "60", "--retries", "2", "--index-url", "https://pypi.org/simple", "--require-hashes", "--only-binary=:all:", "-r", str(lock)], cwd=Path(state), env=env, timeout_seconds=600, code="TOOLCHAIN_BOOTSTRAP_FAILED")
            installed = json.loads(_run([str(python), "-I", "-m", "pip", "--isolated", "list", "--format=json"], cwd=Path(state), env=env, timeout_seconds=30, code="TOOLCHAIN_BOOTSTRAP_FAILED"))
        versions = {package["name"]: package["version"] for package in installed}
        if any(versions.get(name) != expected for name, expected in PINNED_TOOLS.items()):
            raise ToolchainError("TOOLCHAIN_BOOTSTRAP_FAILED", "Installed tool versions differ from the pinned contract")
        receipt = {"tool_bin": str(bin_dir), "python": str(python), "requirements_sha256": _sha256(lock), "installed": installed}
        (prefix / "respan-toolchain-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return receipt
    except BaseException:
        shutil.rmtree(prefix)
        raise
