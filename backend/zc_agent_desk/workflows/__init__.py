from .base import WorkflowRegistry, WorkflowResult
from .keyword_analysis import KeywordAnalysisWorkflow


def default_registry() -> WorkflowRegistry:
    return WorkflowRegistry([KeywordAnalysisWorkflow()])


__all__ = ["WorkflowRegistry", "WorkflowResult", "KeywordAnalysisWorkflow", "default_registry"]
