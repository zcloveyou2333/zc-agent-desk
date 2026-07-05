from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class WorkflowResult:
    content: str
    steps: list[dict[str, Any]]
    clarification: bool = False


class Workflow(Protocol):
    name: str

    def matches(self, message: str) -> bool: ...

    def extract_parameters(self, message: str) -> dict[str, str | None]: ...

    def execute(self, message: str) -> WorkflowResult: ...


class WorkflowRegistry:
    def __init__(self, workflows: list[Workflow]):
        self.workflows = workflows

    def match(self, message: str) -> Workflow | None:
        return next((workflow for workflow in self.workflows if workflow.matches(message)), None)
