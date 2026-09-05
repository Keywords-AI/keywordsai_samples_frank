"""Static requirements-consumer discovery and narrowly scoped SDK delivery repair.

This is deliberately not a shell interpreter. Only literal paths, previously
resolved variables, and the common script-directory idiom are understood.
Unresolved references are evidence for the controller, never guessed paths.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
import re
import shlex
import tomllib
from typing import Iterable


@dataclass(frozen=True)
class RequirementInstall:
    source: str
    line: int
    manifests: tuple[str, ...]
    target: str | None = None


@dataclass(frozen=True)
class RuntimeEntrypoint:
    source: str
    line: int
    kind: str
    target: str
    path: str | None = None
    candidate_path: str | None = None
    working_directory: str | None = None


@dataclass
class DeploymentCatalog:
    installations: list[RequirementInstall] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    entrypoints: list[RuntimeEntrypoint] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_prompt(self) -> str:
        if not self.installations and not self.issues and not self.entrypoints:
            return "No statically resolved requirements-file consumers were found."
        lines = ["Verified requirements consumers (each install has its own dependency closure):"]
        for item in self.installations:
            mode = "isolated/bundled --target install" if item.target else "requirements install"
            lines.append(f"- {item.source}:{item.line}: {mode}; consumes {', '.join(item.manifests)}.")
        if self.entrypoints:
            lines.append("Declared process entrypoints (launch facts, not proof of tracing coverage):")
            for item in self.entrypoints:
                location = item.path or item.candidate_path or "unresolved repository path"
                qualifier = "resolved" if item.path else "candidate only; deployment cwd is unverified"
                lines.append(f"- {item.source}:{item.line}: {item.kind} {item.target}; {location} ({qualifier}).")
            lines.append("Workers and services can reach LLM clients indirectly. Inspect each discovered startup and its called code; do not conclude that a worker needs no tracing because its top-level file has no SDK constructor. Initialize shared tracing from applicable worker/service startups before provider calls. Shared imports may already do this; inspect them rather than duplicating initialization.")
        if self.issues:
            lines.append("Some references could not be resolved statically; inspect their source instead of guessing:")
            lines.extend(f"- {item['source']}:{item['line']}: {item['reason']}" for item in self.issues[:12])
        lines.append("When adding SDK setup to a runtime component, keep every install of that component supplied with the SDK, including bundled installs.")
        return "\n".join(lines)


_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
_VARIABLE = re.compile(r"\$(?:\{([A-Za-z_]\w*)\}|([A-Za-z_]\w*))")
_ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_]\w*)=(.*)$")
_SCRIPT_DIRECTORY = re.compile(
    r"\$\(\s*cd\s+(?:--\s+)?[\"']?\$\(\s*dirname\s+(?:--\s+)?[\"']?"
    r"(?:\$0|\$\{?BASH_SOURCE\[0\]\}?)[\"']?\s*\)[\"']?"
    r"(?P<suffix>(?:/\.\.)*)[\"']?\s*&&\s*pwd\s*\)"
)


def _logical_lines(text: str):
    pending = ""
    start = 1
    for number, line in enumerate(text.splitlines(), 1):
        if not pending:
            start = number
        if line.rstrip().endswith("\\"):
            pending += line.rstrip()[:-1] + " "
        else:
            yield start, pending + line
            pending = ""
    if pending:
        yield start, pending


def _expand(value: str, variables: dict[str, str]) -> str | None:
    def replacement(match):
        name = match.group(1) or match.group(2)
        return variables.get(name, match.group(0))
    value = _VARIABLE.sub(replacement, value)
    return None if "$" in value or "`" in value or "://" in value else value


def _safe_file(root: Path, value: str, base: Path | None = None) -> Path | None:
    """Normalize lexically, rejecting outside paths and every symlink component."""
    path = Path(os.path.abspath((base or root) / value))
    if not path.is_relative_to(root):
        return None
    cursor = root
    for part in path.relative_to(root).parts:
        cursor /= part
        if cursor.is_symlink():
            return None
    return path if path.is_file() else None


def _safe_directory(root: Path, value: str, base: Path) -> Path | None:
    path = Path(os.path.abspath(base / value))
    if not path.is_relative_to(root):
        return None
    cursor = root
    for part in path.relative_to(root).parts:
        cursor /= part
        if cursor.is_symlink():
            return None
    return path if path.is_dir() else None


def _assignment(value: str, source: Path, variables: dict[str, str]) -> str | None:
    raw = value.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        raw = raw[1:-1]
    directory = _SCRIPT_DIRECTORY.fullmatch(raw)
    if directory:
        return os.path.abspath(str(source.parent) + directory.group("suffix"))
    try:
        tokens = shlex.split(value, comments=True)
    except ValueError:
        return None
    return _expand(tokens[0], variables) if len(tokens) == 1 else None


def _tokens(line: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = "#"
        parts = list(lexer)
    except ValueError:
        return []
    result, group = [], []
    for token in parts:
        if token and all(char in ";&|" for char in token):
            if group:
                result.append(group)
            group = []
        else:
            group.append(token)
    if group:
        result.append(group)
    return result


def _install_arguments(tokens: list[str]) -> list[str] | None:
    if tokens and tokens[0] in {"exec", "RUN"}:
        tokens = tokens[1:]
    if len(tokens) >= 2 and Path(tokens[0]).name in {"pip", "pip3"} and tokens[1] == "install":
        return tokens[2:]
    if len(tokens) >= 3 and Path(tokens[0]).name == "uv" and tokens[1:3] == ["pip", "install"]:
        return tokens[3:]
    if len(tokens) >= 4 and tokens[1:4] == ["-m", "pip", "install"] and (tokens[0].startswith("$") or re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", Path(tokens[0]).name)):
        return tokens[4:]
    return None


def _option_values(tokens: list[str], short: str, long: str) -> list[str]:
    values = []
    for index, token in enumerate(tokens):
        if token in {short, long} and index + 1 < len(tokens):
            values.append(tokens[index + 1])
        elif token.startswith(long + "="):
            values.append(token.split("=", 1)[1])
        elif token.startswith(short) and not token.startswith("--") and len(token) > len(short):
            values.append(token[len(short):])
    return values


def _readme_blocks(text: str):
    """Yield shell fences only, retaining source lines and resetting block cwd."""
    active = None
    start = 0
    body = []
    for number, line in enumerate(text.splitlines(), 1):
        fence = re.match(r"^\s*(`{3,}|~{3,})\s*([\w-]*)\s*$", line)
        if active is None:
            if fence and fence[2].lower() in {"sh", "shell", "bash", "zsh", "console", "shell-session"}:
                active = (fence[1][0], len(fence[1]), fence[2].lower())
                start, body = number + 1, []
        elif fence and fence[1][0] == active[0] and len(fence[1]) >= active[1] and not fence[2]:
            yield start, "\n".join(body)
            active = None
        else:
            if active[2] in {"console", "shell-session"}:
                line = line.lstrip()[2:] if line.lstrip().startswith("$ ") else ""
            body.append(line)


def _runtime_target(tokens: list[str]) -> tuple[str, str] | None:
    """Recognize command shape only; never execute or expand its environment."""
    if tokens and tokens[0] == "exec":
        tokens = tokens[1:]
    if not tokens:
        return None
    executable = Path(tokens[0]).name
    python = bool(re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", executable) or re.fullmatch(r"\$\{\w+:-python(?:\d+(?:\.\d+)*)?\}", tokens[0]))
    if python:
        args = tokens[1:]
        while args and args[0] in {"-S", "-s", "-I", "-B", "-u", "-E"}:
            args = args[1:]
        if len(args) >= 2 and args[0] == "-m":
            if args[1] == "uvicorn" and len(args) >= 3 and not args[2].startswith("-"):
                return "asgi-app", args[2]
            if args[1] not in {"pip", "venv", "compileall", "pytest", "unittest"}:
                return "python-module", args[1]
        if args and args[0].endswith(".py"):
            return "python-script", args[0]
    elif executable == "uvicorn" and len(tokens) >= 2 and not tokens[1].startswith("-"):
        return "asgi-app", tokens[1]
    elif executable in {"sh", "bash", "zsh"} and len(tokens) >= 2 and tokens[1].endswith(".sh"):
        return "shell-script", tokens[1]
    elif tokens[0].endswith(".sh"):
        return "shell-script", tokens[0]
    return None


def _record_entrypoint(root: Path, catalog: DeploymentCatalog, source: Path, line: int,
                       tokens: list[str], directories: set[Path], working_directory: str | None):
    target = _runtime_target(tokens)
    if target is None:
        return
    kind, value = target
    if kind in {"python-module", "asgi-app"}:
        module = value.partition(":")[0]
        if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module):
            return
        choices = [module.replace(".", "/") + ".py"]
        if kind == "python-module":
            choices.append(module.replace(".", "/") + "/__main__.py")
    else:
        choices = [value]
    matches = {path for base in directories for choice in choices if (path := _safe_file(root, choice, base)) is not None}
    resolved = next(iter(matches)) if len(matches) == 1 else None
    # An exact checkout-relative match is useful inspection evidence when the
    # deployed cwd is external/unknown. It is explicitly not a resolved launch.
    candidates = {path for choice in choices if (path := _safe_file(root, choice)) is not None}
    candidate = next(iter(candidates)) if resolved is None and len(candidates) == 1 else None
    record = RuntimeEntrypoint(source.relative_to(root).as_posix(), line, kind, value,
                               resolved.relative_to(root).as_posix() if resolved else None,
                               candidate.relative_to(root).as_posix() if candidate else None,
                               working_directory)
    if record not in catalog.entrypoints:
        catalog.entrypoints.append(record)


def _service_entrypoints(root: Path, catalog: DeploymentCatalog, source: Path):
    section, working_directory, commands = None, None, []
    for line, text in _logical_lines(source.read_text(errors="replace")):
        text = text.strip()
        if text.startswith("[") and text.endswith("]"):
            section = text
        elif section == "[Service]":
            name, separator, value = text.partition("=")
            if separator and name == "WorkingDirectory":
                working_directory = value
            elif separator and name == "ExecStart":
                commands.append((line, value))
    directory = _safe_directory(root, working_directory, root) if working_directory else None
    for line, command in commands:
        for tokens in _tokens(command):
            _record_entrypoint(root, catalog, source, line, tokens, {directory} if directory else set(), working_directory)


def discover_consumed_requirements(workdir: Path) -> DeploymentCatalog:
    root = workdir.resolve(strict=True)
    catalog = DeploymentCatalog()
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = sorted(n for n in names if n not in _SKIP_DIRS and not (Path(directory) / n).is_symlink())
        for filename in sorted(files):
            source = Path(directory) / filename
            if source.is_symlink() or source.stat().st_size > 1024 * 1024:
                continue
            readme = filename.lower().startswith("readme") and source.suffix.lower() == ".md"
            if source.suffix == ".service":
                _service_entrypoints(root, catalog, source)
                continue
            if not readme and source.suffix not in {".sh", ".bash", ".zsh", ".yml", ".yaml"} and not (filename.startswith("Dockerfile") or filename in {"Makefile", "makefile"}):
                continue
            content = source.read_text(errors="replace")
            blocks = _readme_blocks(content) if readme else [(1, content)]
            for start, block in blocks:
                variables: dict[str, str] = {}
                # README examples may start at the checkout root or beside the
                # README. Keep both possibilities until a literal cd/file makes
                # the referenced path unique; never prefer a same-named file.
                directories = {root, source.parent} if readme else {root}
                for relative_line, text in _logical_lines(block):
                    line = start + relative_line - 1
                    if not readme and source.suffix not in {".sh", ".bash", ".zsh"}:
                        directories = {root}
                    _scan_line(root, catalog, source, line, text, variables, directories)
    return catalog


def _scan_line(root: Path, catalog: DeploymentCatalog, source: Path, line: int, text: str,
               variables: dict[str, str], directories: set[Path]):
    assignment = _ASSIGNMENT.fullmatch(text)
    if assignment:
        name, value = assignment.groups()
        resolved = _assignment(value, source, variables)
        if resolved is None:
            variables.pop(name, None)
        else:
            variables[name] = resolved
    for tokens in _tokens(text):
        if tokens and tokens[0] == "cd":
            argument = tokens[2:] if len(tokens) > 1 and tokens[1] == "--" else tokens[1:]
            expanded = _expand(argument[0], variables) if len(argument) == 1 else None
            resolved = {path for base in directories if expanded is not None and (path := _safe_directory(root, expanded, base)) is not None}
            directories.clear()
            directories.update(resolved)
            continue
        opaque_context = source.name.startswith("Dockerfile") or source.suffix in {".yml", ".yaml"}
        working_directory = next(iter(directories)).relative_to(root).as_posix() if len(directories) == 1 else None
        _record_entrypoint(root, catalog, source, line, tokens, directories if not opaque_context else set(), working_directory)
        args = _install_arguments(tokens)
        if args is None:
            continue
        references = _option_values(args, "-r", "--requirement")
        manifests = []
        for reference in references:
            expanded = _expand(reference, variables)
            # Docker COPY/build contexts and YAML working-directory settings
            # require another parser. Do not mistake a same-named root file
            # for the file consumed by those runtime contexts.
            absolute = expanded is not None and Path(expanded).is_absolute()
            bases = {root} if absolute else directories if not opaque_context else set()
            paths = {path for base in bases if expanded is not None and (path := _safe_file(root, expanded, base)) is not None}
            path = next(iter(paths)) if len(paths) == 1 else None
            if path is None:
                catalog.issues.append({"source": source.relative_to(root).as_posix(), "line": line, "reason": "requirements reference is unresolved, missing, outside the checkout, or a symlink"})
            else:
                manifests.append(path.relative_to(root).as_posix())
        if manifests:
            target = _option_values(args, "-t", "--target")
            catalog.installations.append(RequirementInstall(source.relative_to(root).as_posix(), line, tuple(dict.fromkeys(manifests)), target[0] if target else None))


def _requirement_identity(line: str) -> tuple[str, str | None] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    match = re.match(r"([A-Za-z0-9_.-]+)(?:\[[^]]+\])?\s*(.*)", line)
    if not match:
        return None
    name = re.sub(r"[-_.]+", "-", match[1]).lower()
    exact = re.match(r"==\s*([^;\s]+)", match[2])
    return name, exact[1] if exact else None


def _marker_tree(requirement: str):
    marker = requirement.split("#", 1)[0].partition(";")[2].strip()
    if not marker:
        return None, set()
    try:
        expression = ast.parse(marker, mode="eval").body
    except SyntaxError as exc:
        raise ValueError("unsupported requirement marker") from exc
    boundaries = set()
    def check(node):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            for item in node.values:
                check(item)
            return
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or not isinstance(node.ops[0], (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
            raise ValueError("unsupported requirement marker")
        sides = (node.left, node.comparators[0])
        names = [item for item in sides if isinstance(item, ast.Name) and item.id == "python_version"]
        literals = [item.value for item in sides if isinstance(item, ast.Constant) and isinstance(item.value, str)]
        if len(names) != 1 or len(literals) != 1 or not re.fullmatch(r"\d+\.\d+", literals[0]):
            raise ValueError("only Python-minor comparison markers are proven here")
        boundaries.add(tuple(map(int, literals[0].split("."))))
    check(expression)
    return expression, boundaries


def _marker_matches(node, version: tuple[int, int]) -> bool:
    if node is None:
        return True
    if isinstance(node, ast.BoolOp):
        values = [_marker_matches(item, version) for item in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    def value(item):
        return version if isinstance(item, ast.Name) else tuple(map(int, item.value.split(".")))
    left, right = value(node.left), value(node.comparators[0])
    return {
        ast.Eq: left == right, ast.NotEq: left != right,
        ast.Lt: left < right, ast.LtE: left <= right,
        ast.Gt: left > right, ast.GtE: left >= right,
    }[type(node.ops[0])]


def _marker_covers(candidate: str, verified: str) -> bool:
    """Prove coverage for Python-minor inequalities, not a guessed target OS.

    Comparisons are constant between their numeric boundaries. Check each
    boundary and adjacent interval; full-version, platform and extra markers
    remain unsupported rather than being evaluated against the host machine.
    """
    try:
        wanted, wanted_boundaries = _marker_tree(verified)
        actual, actual_boundaries = _marker_tree(candidate)
    except ValueError:
        return False
    witnesses = {(0, 0)}
    for major, minor in wanted_boundaries | actual_boundaries:
        witnesses.update({(major, minor), (major, minor + 1), (major, max(0, minor - 1)), (major, 0), (major + 1, 0)})
        if major:
            witnesses.add((major - 1, 0))
    return all(not _marker_matches(wanted, version) or _marker_matches(actual, version) for version in witnesses)


def _closure(root: Path, manifests: Iterable[str]) -> tuple[list[tuple[str, str, int]], list[dict]]:
    entries, issues, seen, active = [], [], set(), set()
    def visit(relative: str):
        if relative in active:
            issues.append({"manifest": relative, "reason": "cyclic requirements include"})
            return
        if relative in seen:
            return
        seen.add(relative)
        path = _safe_file(root, relative)
        if path is None:
            issues.append({"manifest": relative, "reason": "unsafe or missing requirements include"})
            return
        active.add(relative)
        for number, line in _logical_lines(path.read_text()):
            tokens = _tokens(line)
            includes = _option_values(tokens[0], "-r", "--requirement") if tokens else []
            if includes:
                for reference in includes:
                    child = _safe_file(root, reference, path.parent) if _expand(reference, {}) is not None else None
                    if child is None:
                        issues.append({"manifest": relative, "line": number, "reason": "unsafe or unresolved requirements include"})
                    else:
                        visit(child.relative_to(root).as_posix())
            elif _requirement_identity(line):
                entries.append((line, relative, number))
        active.remove(relative)
    for manifest in manifests:
        visit(manifest)
    return entries, issues


def _sdk_status(entries: Iterable[tuple[str, str, int]], package: str, version: str, verified: str) -> tuple[bool, bool]:
    found, conflict = False, False
    for line, _, _ in entries:
        identity = _requirement_identity(line)
        if identity and identity[0] == package:
            covered = identity[1] == version and _marker_covers(line, verified)
            found |= covered
            conflict |= not covered
    return found, conflict


def _anchor(root: Path, relative: str, package: str, version: str, verified: str) -> bool:
    path = _safe_file(root, relative)
    if path is None:
        return False
    if path.name == "pyproject.toml":
        try:
            data = tomllib.loads(path.read_text())
        except tomllib.TOMLDecodeError:
            return False
        dependencies = data.get("project", {}).get("dependencies", [])
        poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        if not isinstance(dependencies, list) or not isinstance(poetry, dict):
            return False
        for name, spec in poetry.items():
            if re.sub(r"[-_.]+", "-", name).lower() == package:
                if isinstance(spec, str):
                    return spec.removeprefix("==") == version
                if not isinstance(spec, dict) or spec.get("optional", False) or str(spec.get("version", "")).removeprefix("==") != version:
                    return False
                if spec.get("platform") or spec.get("extras"):
                    return False
                python = spec.get("python")
                pieces = []
                if python is not None:
                    for part in str(python).split(","):
                        match = re.fullmatch(r"\s*(>=|<=|==|!=|>|<)\s*(\d+\.\d+)\s*", part)
                        if match is None:
                            return False
                        pieces.append(f"python_version {match[1]} '{match[2]}'")
                if spec.get("markers"):
                    pieces.append("(" + str(spec["markers"]) + ")")
                return _marker_covers(f"{package}=={version}; " + " and ".join(pieces), verified)
        found, conflict = _sdk_status(((line, relative, 0) for line in dependencies), package, version, verified)
        return found and not conflict
    if path.suffix not in {".txt", ".in"}:
        return False
    entries, issues = _closure(root, [relative])
    found, conflict = _sdk_status(entries, package, version, verified)
    return found and not conflict and not issues


def _has_respan_setup(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, UnicodeError):
        return False
    return any(isinstance(node, ast.ImportFrom) and node.module == "respan" and any(alias.name == "Respan" for alias in node.names) for node in ast.walk(tree))


def repair_consumed_requirements(workdir: Path, catalog: DeploymentCatalog, changed_files: Iterable[str], verified_requirement: str) -> dict:
    """Add only a missing SDK delivery edge proven by a same-component anchor.

    Delivery must cover every Python-minor interval in the verified requirement.
    This does not prove a whole dependency resolver graph or target-platform
    compatibility. Unconditional pins are allowed for compatible pinned apps.
    """
    root = workdir.resolve(strict=True)
    identity = _requirement_identity(verified_requirement)
    if not identity or identity[0] != "respan-ai" or not identity[1] or "\n" in verified_requirement:
        raise ValueError("An exact verified requirement is required")
    package, version = identity
    _marker_tree(verified_requirement)
    changed = set(changed_files)
    setup_paths = [path for relative in changed if relative.endswith(".py") and (path := _safe_file(root, relative)) is not None and _has_respan_setup(path)]
    # A previously existing declaration is just as useful as one from this
    # patch, but search only known manifests and siblings of the same component.
    known_manifests = {relative for item in catalog.installations for relative in item.manifests}
    anchor_paths = set(changed) | known_manifests
    for relative in known_manifests:
        manifest = _safe_file(root, relative)
        if manifest is None:
            continue
        for sibling in manifest.parent.iterdir():
            if sibling.name == "pyproject.toml" or ("requirements" in sibling.name and sibling.suffix in {".txt", ".in"}):
                anchor_paths.add(sibling.relative_to(root).as_posix())
    anchors = [root / relative for relative in anchor_paths if _anchor(root, relative, package, version, verified_requirement)]
    repairs, issues, checked = [], [], []
    for install in catalog.installations:
        candidates = []
        for relative in install.manifests:
            manifest = root / relative
            if any(path.is_relative_to(manifest.parent) for path in setup_paths):
                candidates.append(relative)
        if not candidates:
            continue
        entries, closure_issues = _closure(root, install.manifests)
        found, conflict = _sdk_status(entries, package, version, verified_requirement)
        evidence = {"source": install.source, "line": install.line, "manifests": list(install.manifests)}
        if closure_issues or conflict:
            issues.append({**evidence, "reason": "requirements closure is unresolved or contains a conflicting SDK requirement", "details": closure_issues})
            continue
        if not found:
            candidates = [relative for relative in candidates if any(anchor.parent == (root / relative).parent for anchor in anchors)]
            if not candidates:
                issues.append({**evidence, "reason": "changed runtime lacks SDK delivery and a verified same-component declaration; no safe repair"})
                continue
            if len(candidates) != 1:
                issues.append({**evidence, "reason": "multiple consumed manifests are eligible; no unique repair target"})
                continue
            destination = _safe_file(root, candidates[0])
            if destination is None:
                issues.append({**evidence, "reason": "repair target is missing or unsafe"})
                continue
            text = destination.read_text()
            destination.write_text(text.rstrip() + "\n\n# Respan SDK for this runtime's tracing setup.\n" + verified_requirement + "\n")
            repairs.append({"path": candidates[0], "requirement": verified_requirement, **evidence})
            entries, closure_issues = _closure(root, install.manifests)
            found, conflict = _sdk_status(entries, package, version, verified_requirement)
        if found and not conflict and not closure_issues:
            checked.append(evidence)
        else:
            issues.append({**evidence, "reason": "SDK requirement is still absent after repair"})
    coverage_uncertainty = []
    if setup_paths:
        for entrypoint in catalog.entrypoints:
            if entrypoint.kind == "shell-script":
                continue
            location = entrypoint.path or entrypoint.candidate_path
            coverage_uncertainty.append({
                **asdict(entrypoint),
                "entrypoint_changed": location in changed if location else None,
                "status": "not_proven_by_static_launcher_inventory",
                "reason": "Inspect startup and shared initialization before indirect provider calls; an unchanged entrypoint may already be covered by a shared import. This is informational, not a failed coverage gate.",
            })
    return {"repairs": repairs, "issues": issues, "checked_installations": checked,
            "discovery_issues": catalog.issues, "entrypoint_coverage_uncertainty": coverage_uncertainty}
