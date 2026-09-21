"""Adapter boundary and deterministic fault-injectable test double."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol
import uuid

from .core import Invalid


class Unsupported(Invalid):
    """Requested capability has no installed adapter; never substitute."""


@dataclass(frozen=True)
class Capabilities:
    mode: str = "live"
    fresh_session: str = "unknown"
    native_identity: str = "unknown"
    tool_disable: str = "unknown"


@dataclass(frozen=True)
class ProbeRequest:
    """Only these fields cross into the target session; no keys or dates."""
    trial_id: str
    prompt: str
    timeout_seconds: float = 60.0


@dataclass
class Capture:
    raw_text: str
    mode: str
    observed: dict[str, Any] = field(default_factory=dict)
    isolation: dict[str, str] = field(default_factory=dict)
    session_id: str | None = None
    latency_ms: float | None = None
    token_usage: dict[str, int | None] = field(default_factory=dict)


class Adapter(Protocol):
    def preflight(self, target: dict[str, Any]) -> Capabilities: ...
    def start(self, target: dict[str, Any], workspace: Path) -> str: ...
    def submit(self, session: str, request: ProbeRequest) -> Capture: ...
    def close(self, session: str | None) -> None: ...


class Registry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[dict[str, Any]], Adapter]] = {}

    def register(self, name: str, factory: Callable[[dict[str, Any]], Adapter]) -> None:
        if not name or name in self._factories:
            raise Invalid(f"Adapter already registered or unnamed: {name}")
        self._factories[name] = factory

    def create(self, target: dict[str, Any]) -> Adapter:
        name = target.get("runtime", {}).get("adapter", "manual")
        if name not in self._factories:
            raise Unsupported(f"No automatic adapter for {name}; manual export/record is available")
        return self._factories[name](target)


class MockAdapter:
    """No network, sleep, credentials, or real model. Faults are deliberate."""
    def __init__(self, response: str = "I do not recognize that reference.",
                 fault: str | None = None, observed: dict[str, Any] | None = None):
        self.response, self.fault = response, fault
        self.observed = observed or {}
        self.calls: list[str] = []
        self.closed = False

    def preflight(self, target: dict[str, Any]) -> Capabilities:
        self.calls.append("preflight")
        if self.fault == "unsupported":
            raise Unsupported("Simulated unsupported capability")
        return Capabilities(mode="mock", fresh_session="supported", tool_disable="supported")

    def start(self, target: dict[str, Any], workspace: Path) -> str:
        self.calls.append("start")
        if self.fault == "start":
            raise RuntimeError("Simulated startup failure")
        if not workspace.is_dir() or any(workspace.iterdir()):
            raise Invalid("Mock workspace must start empty")
        return str(uuid.uuid4())

    def submit(self, session: str, request: ProbeRequest) -> Capture:
        self.calls.append("submit")
        if self.fault == "timeout":
            raise TimeoutError("Simulated deadline expiry; no sleeping")
        if self.fault == "submit":
            raise RuntimeError("Simulated provider failure")
        if self.fault == "cancel":
            raise KeyboardInterrupt()
        observed = {**self.observed, "evidence_source": "mock"}
        return Capture(raw_text="" if self.fault == "empty" else self.response,
                       mode="mock", observed=observed, session_id=session,
                       isolation={"session_fresh": "true", "web_enabled": "false",
                                  "tools_enabled": "false", "system_context_known": "true"},
                       latency_ms=0, token_usage={"input": None, "output": None})

    def close(self, session: str | None) -> None:
        self.calls.append("close")
        self.closed = True
        if self.fault == "close":
            raise RuntimeError("Simulated cleanup failure")


def default_registry() -> Registry:
    registry = Registry()
    registry.register("mock", lambda target: MockAdapter(**target.get("runtime", {}).get("mock", {})))
    return registry
