"""The onboarding config contract.

This is what the questionnaire produces and what the agent implements against — so the
agent never has to guess mid-run. A pre-scan of the repo pre-fills the defaults
(detected language, LLM libraries, frameworks) so the user confirms rather than fills.

Mirrors the SDK's own "Auto vs Full" tracing decision and the gateway credits/BYOK prep.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ControllerConfig(BaseModel):
    """Controller model, optional operator guards, and a hang timeout."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    model: str = Field(
        default="claude-sonnet-5",
        pattern=r"^(?:haiku|sonnet|opus|claude-[A-Za-z0-9._:-]+)$",
    )
    max_turns: int | None = Field(default=None, gt=0, strict=True)
    max_budget_usd: float | None = Field(default=None, gt=0, allow_inf_nan=False, strict=True)
    timeout_seconds: float = Field(default=600, gt=0, allow_inf_nan=False, strict=True)


class Product(str, Enum):
    tracing = "tracing"
    gateway = "gateway"
    both = "both"


# ── Tracing ──────────────────────────────────────────────────────────────────
class TracingMode(str, Enum):
    #: Just `Respan()` — every LLM call captured as a flat span. No decorators,
    #: no framework instrumentor, even if a framework is detected.
    auto = "auto"
    #: Explicit framework instrumentor and/or @workflow/@task decorators.
    full = "full"


class Endpoint(str, Enum):
    platform = "platform"        # https://api.respan.ai
    enterprise = "enterprise"


class TracingConfig(BaseModel):
    mode: TracingMode = TracingMode.auto
    #: Full only — add @workflow/@task decorators for nested structure.
    use_decorators: bool = False
    #: Full only — framework instrumentor to use (auto-detected; e.g.
    #: "respan-instrumentation-langchain"). None = direct-SDK auto only.
    framework_instrumentor: Optional[str] = None
    #: Full + decorators — which workflows to wrap (function names). Empty = agent decides.
    workflows: list[str] = Field(default_factory=list)
    environment: Optional[str] = None    # e.g. "production"
    service_name: Optional[str] = None
    endpoint: Endpoint = Endpoint.platform


# ── Gateway ──────────────────────────────────────────────────────────────────
class GatewayFunding(str, Enum):
    #: Managed provider keys — user adds credits to their Respan account.
    credits = "credits"
    #: Bring your own provider key(s); the gateway proxies them.
    byok = "byok"


class GatewayConfig(BaseModel):
    #: PREP: must be satisfied before implementing, else routed calls fail and the
    #: onboarding demo shows nothing. The runner verifies this up front.
    funding: GatewayFunding
    #: Providers/models to route (e.g. ["openai", "anthropic"]). Empty = OpenAI-compatible passthrough.
    providers: list[str] = Field(default_factory=list)
    enable_caching: bool = False
    enable_fallbacks: bool = False


# ── The request ──────────────────────────────────────────────────────────────
class OnboardingRequest(BaseModel):
    repo_url: str
    base_branch: str = "main"
    product: Product
    tracing: Optional[TracingConfig] = None
    gateway: Optional[GatewayConfig] = None
    controller: ControllerConfig = Field(default_factory=ControllerConfig)

    @model_validator(mode="after")
    def _require_matching_sections(self) -> "OnboardingRequest":
        needs_tracing = self.product in (Product.tracing, Product.both)
        needs_gateway = self.product in (Product.gateway, Product.both)
        if needs_tracing and self.tracing is None:
            self.tracing = TracingConfig()  # sensible default = Auto
        if needs_gateway and self.gateway is None:
            raise ValueError(
                "gateway onboarding requires a GatewayConfig (funding is a required prep step)"
            )
        return self
