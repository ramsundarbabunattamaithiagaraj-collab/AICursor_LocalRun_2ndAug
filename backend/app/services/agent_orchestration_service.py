"""Orchestrates the CrewAI multi-agent SDLC pipeline (Sections 4 & 5).

Runs Business Analyst -> Architect -> Developer -> Tester -> Documentation
agents against a project brief. When no LLM provider is configured (neither
GROQ_API_KEY nor OPENAI_API_KEY set) or the 'crewai' package is unavailable,
each agent returns a clearly labeled deterministic fallback so the platform
remains fully runnable and demoable out of the box (availability-first
default), while still capturing quality metrics and observability data per
Sections 13 and 15.

Provider selection: Groq is preferred when GROQ_API_KEY is configured (fast,
generous free tier); OpenAI is used otherwise. Both go through CrewAI's
built-in LLM class (backed by litellm), so no extra provider-specific SDK is
required beyond 'crewai' itself.
"""
from __future__ import annotations

import time

from app.agents.crew_config import resolve_agents
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.schemas.agents import AgentQualityMetrics, AgentRunResponse, AgentRunResult

logger = get_logger(__name__)


class AgentOrchestrationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _resolve_llm_config(self) -> tuple[str, str, str] | None:
        """Returns (provider, model, api_key) for the first configured provider."""
        if self.settings.groq_api_key:
            return "groq", self.settings.ai_framework.groq_model, self.settings.groq_api_key
        if self.settings.openai_api_key:
            return "openai", self.settings.ai_framework.default_llm, self.settings.openai_api_key
        return None

    def _llm_available(self) -> bool:
        if self._resolve_llm_config() is None:
            return False
        try:
            import crewai  # noqa: F401

            return True
        except ImportError:
            return False

    def run(self, project_brief: str, target_agent: str = "all") -> AgentRunResponse:
        agents = resolve_agents(target_agent)
        if not agents:
            raise ValueError(f"Unknown agent '{target_agent}'.")

        use_llm = self._llm_available()
        results: list[AgentRunResult] = []
        overall_start = time.perf_counter()

        for agent in agents:
            start = time.perf_counter()
            try:
                output = self._run_agent(agent, project_brief, use_llm)
                error = None
            except Exception as exc:  # noqa: BLE001 - never let one agent crash the pipeline
                logger.error("Agent '%s' failed, using fallback output: %s", agent.name, exc)
                output = agent.fallback_output(project_brief)
                error = str(exc)
            elapsed = time.perf_counter() - start

            metrics = self._quality_metrics(output, use_llm and error is None)
            results.append(
                AgentRunResult(
                    agent_name=agent.name,
                    output=output,
                    execution_time_seconds=round(elapsed, 4),
                    quality_metrics=metrics,
                )
            )
            logger.info(
                "agent=%s input_chars=%s output_chars=%s time_s=%.3f confidence=%.2f",
                agent.name, len(project_brief), len(output), elapsed, metrics.confidence_score,
            )

        total_elapsed = time.perf_counter() - overall_start
        return AgentRunResponse(results=results, total_execution_time_seconds=round(total_elapsed, 4))

    def _run_agent(self, agent, project_brief: str, use_llm: bool) -> str:
        if not use_llm:
            return agent.fallback_output(project_brief)

        from crewai import LLM, Crew, Process, Task

        llm_config = self._resolve_llm_config()
        if llm_config is None:
            return agent.fallback_output(project_brief)
        provider, model, api_key = llm_config

        llm = LLM(model=model, temperature=self.settings.ai_framework.temperature, api_key=api_key)
        logger.info("Running agent '%s' via %s (model=%s)", agent.name, provider, model)
        crewai_agent = agent.build_crewai_agent(llm)
        task = Task(
            description=agent.task_description(project_brief),
            expected_output=f"A detailed {agent.name} deliverable in Markdown.",
            agent=crewai_agent,
        )
        crew = Crew(agents=[crewai_agent], tasks=[task], process=Process.sequential, verbose=False)
        result = crew.kickoff()
        return str(result)

    @staticmethod
    def _quality_metrics(output: str, llm_backed: bool) -> AgentQualityMetrics:
        """Heuristic quality scoring (Section 15).

        Real LLM-backed output is scored higher-confidence than the
        deterministic fallback, and length/structure act as simple proxies
        for completeness. Explanation text documents how each score was
        derived, as required.
        """
        length_score = min(1.0, len(output) / 800)
        has_structure = ("##" in output or "-" in output)
        completeness = round(0.5 * length_score + 0.5 * (1.0 if has_structure else 0.0), 3)
        confidence = round(0.85 if llm_backed else 0.55, 3)
        hallucination_risk = round(0.15 if llm_backed else 0.35, 3)
        requirement_coverage = round(min(1.0, 0.4 + 0.6 * length_score), 3)
        context_relevance = round(0.8 if llm_backed else 0.6, 3)

        explanation = (
            f"confidence_score derived from generation mode (llm_backed={llm_backed}); "
            f"completeness = 0.5*length_ratio({length_score:.2f}) + 0.5*has_markdown_structure({has_structure}); "
            f"hallucination_risk is lower for LLM-backed output but never assumed to be zero; "
            f"requirement_coverage and context_relevance are heuristic proxies pending human review."
        )

        return AgentQualityMetrics(
            confidence_score=confidence,
            hallucination_risk=hallucination_risk,
            requirement_coverage=requirement_coverage,
            context_relevance=context_relevance,
            completeness=completeness,
            explanation=explanation,
        )


def get_agent_orchestration_service() -> AgentOrchestrationService:
    return AgentOrchestrationService()
