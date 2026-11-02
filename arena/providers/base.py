"""Provider adapter contract.

Adapters own provider-specific API calls. Workloads and result serialization
stay provider-neutral. A future adapter can wrap E2B, Daytona, Modal, a local
microVM, or any other runtime without changing the benchmark runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence


@dataclass
class SandboxHandle:
    provider_id: str
    native_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderAdapter(Protocol):
    id: str

    def create(self, workload: dict[str, Any]) -> SandboxHandle:
        ...

    def execute(self, handle: SandboxHandle, command: Sequence[str], timeout_seconds: int) -> dict[str, Any]:
        ...

    def destroy(self, handle: SandboxHandle) -> None:
        ...

