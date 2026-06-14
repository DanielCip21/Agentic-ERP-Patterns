"""Unified orchestrator that routes tasks across all five live platform agents."""

from __future__ import annotations

import asyncio
from typing import Any

import anthropic

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.ai.azure_ai_agent import AzureAIAgent
from agentic_erp.api.power_platform_agent import PowerPlatformAgent
from agentic_erp.connectors.azure_ai import AzureAIConfig
from agentic_erp.connectors.dataverse import DataverseConfig
from agentic_erp.connectors.dynamics365 import Dynamics365Config
from agentic_erp.connectors.power_platform import PowerPlatformConfig
from agentic_erp.connectors.salesforce import SalesforceConfig
from agentic_erp.crm.salesforce_crm_agent import SalesforceCRMAgent
from agentic_erp.erp.dataverse_agent import DataverseAgent
from agentic_erp.erp.dynamics365_order_agent import Dynamics365OrderAgent
from agentic_erp.patterns.circuit_breaker import CircuitBreaker


# Keywords used to fast-route a task to the relevant platform(s).
_PLATFORM_KEYWORDS: dict[str, set[str]] = {
    "dynamics365": {"dynamics", "d365", "crm", "order", "orders", "opportunity", "opportunities"},
    "salesforce": {"salesforce", "sfdc", "soql", "sf"},
    "power_platform": {"flow", "flows", "automate", "trigger", "power automate"},
    "azure_ai": {"document", "invoice", "embed", "embedding", "vector", "openai", "gpt", "analyze", "analyse", "search"},
    "dataverse": {"dataverse", "fetchxml", "odata", "entity", "association"},
}

_CIRCUIT_OPEN_MSG = "[UNAVAILABLE] {name} circuit is open — too many recent failures. Will retry after recovery timeout."


class LivePlatformOrchestrator:
    """Routes a task to the right live platform agent(s) and aggregates results.

    Accepts optional configs for each platform. Only configured platforms participate.

    Features:
    - Keyword routing selects the right platform(s) per task
    - Per-platform circuit breakers protect against cascading failures
    - Parallel async dispatch via ``run_async`` / ``run_and_synthesize_async``
    - Claude synthesis merges multi-platform responses into a single answer

    Usage::

        from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator

        orch = LivePlatformOrchestrator(
            dynamics365_config=Dynamics365Config(...),
            salesforce_config=SalesforceConfig(...),
            azure_ai_config=AzureAIConfig(...),
        )

        # Per-platform dict (sequential, circuit-protected)
        results = orch.run("List open opportunities in both D365 and Salesforce.")

        # Parallel + synthesized (async, circuit-protected)
        import asyncio
        answer = asyncio.run(orch.run_and_synthesize_async(
            "Compare CRM pipeline across Dynamics 365 and Salesforce for Q1."
        ))
    """

    def __init__(
        self,
        dynamics365_config: Dynamics365Config | None = None,
        salesforce_config: SalesforceConfig | None = None,
        power_platform_config: PowerPlatformConfig | None = None,
        azure_ai_config: AzureAIConfig | None = None,
        dataverse_config: DataverseConfig | None = None,
        client: anthropic.Anthropic | None = None,
        model: str = BaseERPAgent.DEFAULT_MODEL,
        breaker_failure_threshold: int = 3,
        breaker_recovery_timeout: float = 60.0,
    ) -> None:
        self._client = client or anthropic.Anthropic()
        self._model = model
        self._agents: dict[str, BaseERPAgent] = {}

        if dynamics365_config:
            self._agents["dynamics365"] = Dynamics365OrderAgent(dynamics365_config, client=self._client)
        if salesforce_config:
            self._agents["salesforce"] = SalesforceCRMAgent(salesforce_config, client=self._client)
        if power_platform_config:
            self._agents["power_platform"] = PowerPlatformAgent(power_platform_config, client=self._client)
        if azure_ai_config:
            self._agents["azure_ai"] = AzureAIAgent(azure_ai_config, client=self._client)
        if dataverse_config:
            self._agents["dataverse"] = DataverseAgent(dataverse_config, client=self._client)

        if not self._agents:
            raise ValueError("At least one platform config must be provided.")

        self._breakers: dict[str, CircuitBreaker] = {
            name: CircuitBreaker(
                failure_threshold=breaker_failure_threshold,
                recovery_timeout=breaker_recovery_timeout,
            )
            for name in self._agents
        }

    @property
    def configured_platforms(self) -> list[str]:
        """Names of all currently configured platforms."""
        return list(self._agents)

    @property
    def platform_status(self) -> dict[str, str]:
        """Circuit breaker state per platform: 'closed', 'open', or 'half_open'."""
        return {name: breaker.state.value for name, breaker in self._breakers.items()}

    def _select_agents(self, task: str) -> list[str]:
        """Keyword-route the task to a subset of configured platforms.

        Falls back to all configured platforms when no keywords match.
        """
        task_lower = task.lower()
        words = set(task_lower.split())
        matched = [
            name for name, keywords in _PLATFORM_KEYWORDS.items()
            if name in self._agents and (
                words & keywords
                or any(k in task_lower for k in keywords if " " in k)
            )
        ]
        return matched or list(self._agents)

    def _run_agent_safe(self, name: str, task: str) -> str:
        """Run a single agent with circuit-breaker protection."""
        breaker = self._breakers[name]
        if not breaker.is_available:
            return _CIRCUIT_OPEN_MSG.format(name=name)
        try:
            result = self._agents[name].run(task)
            breaker.record_success()
            return result
        except Exception as exc:
            breaker.record_failure()
            return f"[ERROR] {name} failed: {exc}"

    async def _run_agent_safe_async(self, name: str, task: str) -> tuple[str, str]:
        """Async circuit-protected agent call for use with asyncio.gather."""
        breaker = self._breakers[name]
        if not breaker.is_available:
            return name, _CIRCUIT_OPEN_MSG.format(name=name)
        try:
            result = await asyncio.to_thread(self._agents[name].run, task)
            breaker.record_success()
            return name, result
        except Exception as exc:
            breaker.record_failure()
            return name, f"[ERROR] {name} failed: {exc}"

    def run_platform(self, platform: str, task: str) -> str:
        """Run a single named platform agent with circuit-breaker protection.

        Raises ``ValueError`` when *platform* is not configured.
        """
        if platform not in self._agents:
            raise ValueError(
                f"Platform {platform!r} is not configured. "
                f"Available: {list(self._agents)}"
            )
        return self._run_agent_safe(platform, task)

    async def run_platform_async(self, platform: str, task: str) -> str:
        """Async version of ``run_platform``."""
        if platform not in self._agents:
            raise ValueError(
                f"Platform {platform!r} is not configured. "
                f"Available: {list(self._agents)}"
            )
        _, result = await self._run_agent_safe_async(platform, task)
        return result

    def stream_platform(self, platform: str, task: str):
        """Yield text chunks from a single platform agent (generator).

        Applies circuit-breaker protection; yields a single ``[ERROR]`` string
        on failure rather than propagating the exception.
        """
        if platform not in self._agents:
            raise ValueError(
                f"Platform {platform!r} is not configured. "
                f"Available: {list(self._agents)}"
            )
        breaker = self._breakers[platform]
        if not breaker.is_available:
            yield _CIRCUIT_OPEN_MSG.format(name=platform)
            return
        try:
            yield from self._agents[platform].stream(task)
            breaker.record_success()
        except Exception as exc:
            breaker.record_failure()
            yield f"[ERROR] {platform} failed: {exc}"

    def run(self, task: str) -> dict[str, str]:
        """Route *task* to matched agents and return ``{platform: response}``.

        Open circuit breakers are skipped and flagged in the result dict.
        Agent exceptions are caught, recorded against the breaker, and returned
        as ``[ERROR]`` strings so one platform's failure never kills the call.
        """
        targets = self._select_agents(task)
        return {name: self._run_agent_safe(name, task) for name in targets}

    async def run_async(self, task: str) -> dict[str, str]:
        """Parallel version of ``run()`` — matched agents execute concurrently.

        Uses ``asyncio.to_thread`` to run sync agents in a thread pool so all
        network round-trips overlap. Latency = ``max(agent latencies)`` rather
        than their sum. Circuit-protected: open platforms are skipped.
        """
        targets = self._select_agents(task)
        pairs = await asyncio.gather(
            *[self._run_agent_safe_async(name, task) for name in targets]
        )
        return dict(pairs)

    async def run_and_synthesize_async(self, task: str) -> str:
        """Parallel dispatch + async Claude synthesis.

        Agents run concurrently; synthesis is a non-blocking thread-pool call.
        Falls back to the single response when only one platform matched.
        """
        platform_results = await self.run_async(task)

        if len(platform_results) == 1:
            return next(iter(platform_results.values()))

        combined = "\n\n".join(
            f"[{name.upper()}]\n{resp}" for name, resp in platform_results.items()
        )
        synthesis_prompt = (
            f"The following responses were gathered from multiple platform agents "
            f"for this task: {task!r}\n\n{combined}\n\n"
            "Synthesize these into a single clear, concise answer. "
            "Call out any cross-platform insights, conflicts, or gaps."
        )
        response = await asyncio.to_thread(
            lambda: self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                messages=[{"role": "user", "content": synthesis_prompt}],
            )
        )
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return combined

    def run_and_synthesize(self, task: str) -> str:
        """Like ``run()`` but asks Claude to write a single unified answer.

        If only one platform matched, returns its response directly (no extra API call).
        """
        platform_results = self.run(task)

        if len(platform_results) == 1:
            return next(iter(platform_results.values()))

        combined = "\n\n".join(
            f"[{name.upper()}]\n{resp}" for name, resp in platform_results.items()
        )
        synthesis_prompt = (
            f"The following responses were gathered from multiple platform agents "
            f"for this task: {task!r}\n\n{combined}\n\n"
            "Synthesize these into a single clear, concise answer. "
            "Call out any cross-platform insights, conflicts, or gaps."
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return combined
