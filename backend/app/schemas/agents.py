from __future__ import annotations

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    project_brief: str = Field(..., min_length=10, max_length=5000)
    target_agent: str = Field(
        default="all",
        pattern="^(all|business_analyst|architect|developer|tester|documentation)$",
    )


class AgentQualityMetrics(BaseModel):
    confidence_score: float
    hallucination_risk: float
    requirement_coverage: float
    context_relevance: float
    completeness: float
    explanation: str


class AgentRunResult(BaseModel):
    agent_name: str
    output: str
    execution_time_seconds: float
    quality_metrics: AgentQualityMetrics


class AgentRunResponse(BaseModel):
    results: list[AgentRunResult]
    total_execution_time_seconds: float
