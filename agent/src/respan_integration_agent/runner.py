"""Session orchestrator: validate → (prep) → clone → agent → PR.

The request carries an explicit controller model, turn limit, SDK budget, and timeout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import base64
import json
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from . import github
from .agent import run_agent, _git_changed, PYTHON_SDK_CONDITIONAL_DEPENDENCY
from .config import OnboardingRequest, Product, TracingMode
from .deployment import discover_consumed_requirements, repair_consumed_requirements
from .sandbox import checkout
from .skill import validate_skill_source
from .toolchain import ToolchainError, preflight_toolchain, finalize_lockfiles


@dataclass
class SessionResult:
    summary: str
    trace_id: str | None
    changed_files: list[str]
    diff: str
    pr: github.OpenedPR | None  # None in v0a (no token → no PR, just the diff)
    validation_errors: list[str] = field(default_factory=list)
    setup_receipt: dict = field(default_factory=dict)
    delivery_receipt: dict = field(default_factory=dict)


def _preflight(req: OnboardingRequest) -> None:
    """Fail fast on prep the onboarding depends on.

    Gateway onboarding is worthless if the account can't route a call, so verify funding
    (credits balance > 0, or BYOK keys present) BEFORE we clone or spend a token on the agent.
    """
    if req.product in (Product.gateway, Product.both):
        # TODO(v0): call the Respan API to confirm credits balance > 0 (or BYOK configured).
        # Raise a clear error the dashboard can surface ("add credits before onboarding").
        pass


def run_session(
    req: OnboardingRequest, *, respan_api_key: str, github_token: str | None = None
) -> SessionResult:
    _preflight(req)
    validate_skill_source()
    if github_token is not None:
        github.parse_repository(req.repo_url)
        if not github_token:
            raise github.GitHubDeliveryError("A nonempty GitHub token is required for v0b.")
    branch = f"respan/onboard-{req.product.value}-{uuid4().hex}"
    title = f"Add Respan {req.product.value} instrumentation"
    delivery = {}
    with checkout(req.repo_url, req.base_branch, token=github_token) as workdir:
        identity = github.capture_checkout_identity(workdir) if github_token else None
        # Missing tools are an operator setup failure, before any paid model call.
        toolchain = preflight_toolchain(workdir)
        deployment = discover_consumed_requirements(workdir)
        setup_context = "Lock tools verified by the runner: " + json.dumps(toolchain.to_dict())
        setup_context += "\n" + deployment.to_prompt()
        result = run_agent(
            workdir, req, respan_api_key=respan_api_key,
            **req.controller.model_dump(),
            setup_context=setup_context,
        )
        if identity:
            github.verify_checkout_identity(workdir, identity)
        if not result.changed_files:
            raise RuntimeError("agent produced no changes")
        errors = []
        setup = {"toolchain": toolchain.to_dict(), "deployment": deployment.to_dict()}
        if req.tracing and req.tracing.mode is TracingMode.auto:
            current_deployment = discover_consumed_requirements(workdir)
            dependency_delivery = repair_consumed_requirements(
                workdir, current_deployment, result.changed_files, PYTHON_SDK_CONDITIONAL_DEPENDENCY,
            )
            setup["deployment_after_edits"] = current_deployment.to_dict()
            setup["dependency_delivery"] = dependency_delivery
            errors.extend(str(issue) for issue in dependency_delivery["issues"])
        if not errors:
            try:
                setup["lock_finalization"] = finalize_lockfiles(
                    workdir, toolchain, timeout_seconds=600,
                )
            except ToolchainError as exc:
                errors.append(str(exc))
        # Trusted finalization can add requirements/locks after the model's result.
        if identity:
            github.verify_checkout_identity(workdir, identity)
        changed_files = _git_changed(workdir)
        diff = _git_diff(workdir)
        pr = None
        summary = result.summary
        output = {"diff": diff, "summary": summary, "changed_files": changed_files, "setup": setup, "errors": errors}
        safe = _redact_output(output, respan_api_key, github_token)
        file_secret = _changed_file_contains_secret(workdir, changed_files, respan_api_key, github_token)
        if safe != output or file_secret:
            diff, summary, changed_files, setup, errors = (safe[name] for name in ("diff", "summary", "changed_files", "setup", "errors"))
            if file_secret:
                diff = "[REDACTED] Patch withheld because generated files contain credentials.\n"
            errors.append("SECRET_IN_GENERATED_OUTPUT: publishing is blocked; output has been redacted.")
        if github_token and not errors:  # Block PR delivery of incomplete dependency setup.
            delivery = {"repository": github.parse_repository(req.repo_url).full_name,
                        "base_branch": req.base_branch, "base_sha": identity["base_sha"],
                        "branch": branch, "head_sha": None, "branch_pushed": False}
            try:
                # Never grant publishing credentials to the model-edited checkout.
                with checkout(req.repo_url, req.base_branch, token=github_token) as trusted:
                    if github.authenticated_git(trusted, "rev-parse", "HEAD") != identity["base_sha"]:
                        raise github.GitHubDeliveryError("Base branch moved during generation; review the retained diff before retrying.")
                    github.authenticated_git(trusted, "apply", "--index", "--binary", "--whitespace=nowarn", "-", input_text=diff)
                    if _git_diff(trusted) != diff:
                        raise github.GitHubDeliveryError("Replayed patch does not match the finalized diff.")
                    head = github.commit_branch(trusted, branch, title)
                    delivery["head_sha"] = head
                    delivery["tree_sha"] = github.authenticated_git(trusted, "rev-parse", "HEAD^{tree}")
                    body = _pr_body(summary, result.trace_id, identity["base_sha"])
                    pr = github.open_pr(trusted, branch, title, body, github_token,
                                        repo_url=req.repo_url, base_branch=req.base_branch, head_sha=head)
                    delivery.update(branch_pushed=True, pr_url=pr.url, pr_number=pr.number)
            except github.GitHubDeliveryError as exc:
                delivery["head_sha"] = exc.head_sha or delivery["head_sha"]
                delivery["branch_pushed"] = exc.branch_pushed
                errors.append(f"PR_DELIVERY_FAILED: {exc}")
    return SessionResult(
        summary=summary,
        trace_id=result.trace_id,
        changed_files=changed_files,
        diff=diff,
        pr=pr,
        validation_errors=errors,
        setup_receipt=setup,
        delivery_receipt=delivery,
    )


def _secret_forms(*secrets: str | None) -> set[str]:
    forms = set()
    for secret in filter(None, secrets):
        forms.update({secret, quote(secret, safe=""), base64.b64encode(secret.encode()).decode(),
                      base64.b64encode(f"x-access-token:{secret}".encode()).decode()})
    return forms


def _changed_file_contains_secret(workdir: Path, names: list[str], *secrets: str | None) -> bool:
    # Binary Git patches encode file content; scanning their text alone misses secrets.
    forms = {form.encode() for form in _secret_forms(*secrets)}
    if not forms:
        return False
    overlap = max(map(len, forms)) - 1
    for name in names:
        path = workdir / name
        if path.is_symlink() or not path.is_file():
            continue
        if not path.resolve().is_relative_to(workdir.resolve()):
            raise github.GitHubDeliveryError("Generated file leaves the checkout; publishing is blocked.")
        with path.open("rb") as stream:
            tail = b""
            while chunk := stream.read(65536):
                data = tail + chunk
                if any(form in data for form in forms):
                    return True
                tail = data[-overlap:] if overlap else b""
    return False


def _redact_secrets(text: str, *secrets: str | None) -> str:
    for form in _secret_forms(*secrets):
        text = text.replace(form, "[REDACTED]")
    return text


def _redact_output(value, *secrets: str | None):
    if isinstance(value, str):
        return _redact_secrets(value, *secrets)
    if isinstance(value, dict):
        return {_redact_output(key, *secrets): _redact_output(item, *secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_output(item, *secrets) for item in value]
    return value


def _pr_body(summary: str, trace_id: str | None, base_sha: str) -> str:
    body = summary[:12000].strip() + "\n\n"
    body += "Generated by Respan onboarding from base `" + base_sha + "`.\n\n"
    body += "- [x] Generated patch and dependency setup checked by the runner.\n"
    body += "- [ ] Configure `RESPAN_API_KEY` in the application's runtime environment.\n"
    body += "- [ ] Run the application and verify its trace contents before merging.\n"
    if trace_id:
        body += "\nController trace: `" + trace_id + "` (this is not target application acceptance).\n"
    return body


def _git_diff(workdir) -> str:
    import tempfile

    # Include new files and staged edits without changing the checkout's real index.
    with tempfile.TemporaryDirectory(prefix="respan-diff-") as tmp:
        index = Path(tmp) / "index"
        for args in (["read-tree", "HEAD"], ["add", "--all", "--", "."]):
            github.authenticated_git(workdir, *args, index_file=index)
        return github.authenticated_git(
            workdir, "diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv", "HEAD", "--",
            index_file=index, strip=False,
        )
