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


# Keywords used to fast-route a task to the relevant platform(s).
_PLATFORM_KEYWORDS: dict[str, set[str]] = {
    "dynamics365": {"dynamics", "d365", "crm", "order", "orders", "opportunity", "opportunities"},
    "salesforce": {"salesforce", "sfdc", "soql", "sf"},
    "power_platform": {"flow", "flows", "automate", "trigger", "power automate"},
    "azure_ai": {"document", "invoice", "embed", "embedding", "vector", "openai", "gpt", "analyze", "analyse", "search"},
    "dataverse": {"dataverse", "fetchxml", "odata", "entity", "association"},
}


class LivePlatformOrchestrator:
    """Routes a task to the right live platform agent(s) and aggregates results.

    Accepts optional configs for each platform. Only configured platforms participate.
    Use ``run()`` for per-platform results or ``run_and_synthesize()`` for a single
    Claude-written summary that spans all platforms.

    Usage::

        from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator

        orch = LivePlatformOrchestrator(
            dynamics365_config=Dynamics365Config(...),
            salesforce_config=SalesforceConfig(...),
            azure_ai_config=AzureAIConfig(...),
        )

        # Per-platform dict
        results = orch.run("List open opportunities in both D365 and Salesforce.")

        # Single synthesized answer
        answer = orch.run_and_synthesize(
            "Compare CRM pipeline across Dynamics 365 and Salesforce for Q1."
        )
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

    @property
    def configured_platforms(self) -> list[str]:
        """Names of all currently configured platforms."""
        return list(self._agents)

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

    def run(self, task: str) -> dict[str, str]:
        """Route *task* to matched agents and return ``{platform: response}``."""
        targets = self._select_agents(task)
        return {name: self._agents[name].run(task) for name in targets}

    async def run_async(self, task: str) -> dict[str, str]:
        """Parallel version of ``run()`` — matched agents execute concurrently.

        Uses ``asyncio.to_thread`` to run sync agents in a thread pool so all
        network round-trips overlap. Latency = ``max(agent latencies)`` rather
        than their sum.
        """
        targets = self._select_agents(task)
        responses = await asyncio.gather(
            *[asyncio.to_thread(self._agents[name].run, task) for name in targets]
        )
        return dict(zip(targets, responses))

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
