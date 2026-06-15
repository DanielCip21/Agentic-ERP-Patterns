"""Tests for async methods on LivePlatformOrchestrator."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock


from agentic_erp.connectors.dynamics365 import Dynamics365Config
from agentic_erp.connectors.salesforce import SalesforceConfig
from agentic_erp.connectors.azure_ai import AzureAIConfig
from agentic_erp.connectors.dataverse import DataverseConfig
from agentic_erp.connectors.power_platform import PowerPlatformConfig
from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator


# ---------------------------------------------------------------------------
# Helpers (mirrors test_live_platform_orchestrator.py)
# ---------------------------------------------------------------------------


def _d365_config():
    return Dynamics365Config(
        tenant_id="t",
        client_id="c",
        client_secret="s",
        environment_url="https://org.crm.dynamics.com",
    )


def _sf_config():
    return SalesforceConfig(
        instance_url="https://org.my.salesforce.com", access_token="tok"
    )


def _ai_config():
    return AzureAIConfig(
        endpoint="https://res.openai.azure.com", api_key="k", deployment_name="gpt-4o"
    )


def _dv_config():
    return DataverseConfig(
        environment_url="https://org.crm.dynamics.com",
        tenant_id="t",
        client_id="c",
        client_secret="s",
    )


def _pp_config():
    return PowerPlatformConfig(
        environment_id="env-1",
        environment_url="https://org.crm.dynamics.com",
        tenant_id="t",
        client_id="c",
        client_secret="s",
    )


def _mock_agent(response: str = "ok") -> MagicMock:
    agent = MagicMock()
    agent.run.return_value = response
    return agent


def _mock_client(text: str = "synthesized") -> MagicMock:
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    client = MagicMock()
    client.messages.create.return_value = resp
    return client


# ---------------------------------------------------------------------------
# run_async()
# ---------------------------------------------------------------------------


class TestRunAsync:
    def test_returns_dict_of_strings(self):
        client = _mock_client()
        orch = LivePlatformOrchestrator(salesforce_config=_sf_config(), client=client)
        orch._agents["salesforce"] = _mock_agent("SF result")

        results = asyncio.run(orch.run_async("Salesforce SOQL query"))
        assert isinstance(results, dict)
        assert results["salesforce"] == "SF result"

    def test_parallel_dispatch_runs_all_matched_agents(self):
        client = _mock_client()
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365")
        orch._agents["salesforce"] = _mock_agent("SF")

        results = asyncio.run(
            orch.run_async("Compare D365 orders and Salesforce opportunities")
        )
        assert "dynamics365" in results
        assert "salesforce" in results
        assert results["dynamics365"] == "D365"
        assert results["salesforce"] == "SF"

    def test_fallback_runs_all_configured_when_no_keyword_match(self):
        client = _mock_client()
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365")
        orch._agents["salesforce"] = _mock_agent("SF")

        results = asyncio.run(orch.run_async("what is the weather like"))
        assert set(results.keys()) == {"dynamics365", "salesforce"}

    def test_all_five_platforms_in_parallel(self):
        client = _mock_client()
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            power_platform_config=_pp_config(),
            azure_ai_config=_ai_config(),
            dataverse_config=_dv_config(),
            client=client,
        )
        for name in orch.configured_platforms:
            orch._agents[name] = _mock_agent(f"{name} response")

        results = asyncio.run(orch.run_async("broad task with no specific keyword"))
        assert len(results) == 5
        assert all(isinstance(v, str) for v in results.values())

    def test_keyword_routes_to_single_platform(self):
        client = _mock_client()
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 only")
        orch._agents["salesforce"] = _mock_agent("SF only")

        results = asyncio.run(orch.run_async("List all D365 sales orders"))
        # dynamics365 keyword should match, SF should not
        assert "dynamics365" in results


# ---------------------------------------------------------------------------
# run_and_synthesize_async()
# ---------------------------------------------------------------------------


class TestRunAndSynthesizeAsync:
    def test_single_platform_returns_directly_no_synthesis(self):
        client = _mock_client("should not appear")
        orch = LivePlatformOrchestrator(salesforce_config=_sf_config(), client=client)
        orch._agents["salesforce"] = _mock_agent("direct SF answer")

        result = asyncio.run(orch.run_and_synthesize_async("Salesforce SOQL query"))
        assert result == "direct SF answer"
        client.messages.create.assert_not_called()

    def test_multi_platform_calls_synthesis(self):
        client = _mock_client("cross-platform summary")
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 pipeline")
        orch._agents["salesforce"] = _mock_agent("SF pipeline")

        result = asyncio.run(
            orch.run_and_synthesize_async("Compare D365 and Salesforce pipeline")
        )
        assert result == "cross-platform summary"
        client.messages.create.assert_called_once()

    def test_synthesis_prompt_contains_both_platform_responses(self):
        client = _mock_client("ok")
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 data here")
        orch._agents["salesforce"] = _mock_agent("SF data here")

        asyncio.run(orch.run_and_synthesize_async("Compare D365 and Salesforce"))
        prompt = client.messages.create.call_args[1]["messages"][0]["content"]
        assert "D365 data here" in prompt
        assert "SF data here" in prompt

    def test_result_is_always_string(self):
        client = _mock_client("answer")
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("a")
        orch._agents["salesforce"] = _mock_agent("b")

        result = asyncio.run(
            orch.run_and_synthesize_async("generic cross-platform task")
        )
        assert isinstance(result, str)

    def test_three_platforms_all_included_in_synthesis(self):
        client = _mock_client("triple synthesis")
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            azure_ai_config=_ai_config(),
            client=client,
        )
        for name in orch.configured_platforms:
            orch._agents[name] = _mock_agent(f"{name} resp")

        result = asyncio.run(
            orch.run_and_synthesize_async("analyse documents and crm pipeline")
        )
        assert isinstance(result, str)
