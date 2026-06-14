"""Tests for LivePlatformOrchestrator — all HTTP and Claude calls are mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentic_erp.connectors.azure_ai import AzureAIConfig
from agentic_erp.connectors.dataverse import DataverseConfig
from agentic_erp.connectors.dynamics365 import Dynamics365Config
from agentic_erp.connectors.power_platform import PowerPlatformConfig
from agentic_erp.connectors.salesforce import SalesforceConfig
from agentic_erp.patterns.circuit_breaker import CircuitBreaker, CircuitState
from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _d365_config() -> Dynamics365Config:
    return Dynamics365Config(
        tenant_id="t", client_id="c", client_secret="s",
        environment_url="https://org.crm.dynamics.com",
    )

def _sf_config() -> SalesforceConfig:
    return SalesforceConfig(instance_url="https://org.my.salesforce.com", access_token="tok")

def _pp_config() -> PowerPlatformConfig:
    return PowerPlatformConfig(
        environment_id="env-1", environment_url="https://org.crm.dynamics.com",
        tenant_id="t", client_id="c", client_secret="s",
    )

def _ai_config() -> AzureAIConfig:
    return AzureAIConfig(endpoint="https://res.openai.azure.com", api_key="k", deployment_name="gpt-4o")

def _dv_config() -> DataverseConfig:
    return DataverseConfig(
        environment_url="https://org.crm.dynamics.com",
        tenant_id="t", client_id="c", client_secret="s",
    )

def _mock_agent(response: str = "ok") -> MagicMock:
    """Return a fake agent whose run() always returns *response*."""
    agent = MagicMock()
    agent.run.return_value = response
    return agent

def _mock_client(text: str = "synthesized answer") -> MagicMock:
    """Return a fake Anthropic client whose messages.create() returns *text*."""
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    client = MagicMock()
    client.messages.create.return_value = resp
    return client


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestLivePlatformOrchestratorConstruction:
    def test_raises_with_no_configs(self):
        with pytest.raises(ValueError, match="At least one"):
            LivePlatformOrchestrator()

    def test_single_platform_configured(self):
        orch = LivePlatformOrchestrator(salesforce_config=_sf_config(), client=_mock_client())
        assert orch.configured_platforms == ["salesforce"]

    def test_all_five_platforms_configured(self):
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            power_platform_config=_pp_config(),
            azure_ai_config=_ai_config(),
            dataverse_config=_dv_config(),
            client=_mock_client(),
        )
        assert set(orch.configured_platforms) == {
            "dynamics365", "salesforce", "power_platform", "azure_ai", "dataverse"
        }


# ---------------------------------------------------------------------------
# _select_agents routing
# ---------------------------------------------------------------------------

class TestSelectAgents:
    def _orch(self) -> LivePlatformOrchestrator:
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            power_platform_config=_pp_config(),
            azure_ai_config=_ai_config(),
            dataverse_config=_dv_config(),
            client=_mock_client(),
        )
        return orch

    def test_routes_dynamics365_keyword(self):
        orch = self._orch()
        assert "dynamics365" in orch._select_agents("List all D365 orders")

    def test_routes_salesforce_keyword(self):
        orch = self._orch()
        assert "salesforce" in orch._select_agents("Run a SOQL query on Salesforce leads")

    def test_routes_power_platform_keyword(self):
        orch = self._orch()
        assert "power_platform" in orch._select_agents("Trigger a flow in Power Automate")

    def test_routes_azure_ai_keyword(self):
        orch = self._orch()
        assert "azure_ai" in orch._select_agents("Analyze this invoice document")

    def test_routes_dataverse_keyword(self):
        orch = self._orch()
        assert "dataverse" in orch._select_agents("Run a FetchXML query on the dataverse table")

    def test_fallback_to_all_when_no_keyword_matches(self):
        orch = self._orch()
        result = orch._select_agents("generic task with no specific platform keywords")
        assert set(result) == set(orch.configured_platforms)

    def test_routes_only_configured_platforms(self):
        orch = LivePlatformOrchestrator(
            salesforce_config=_sf_config(), client=_mock_client()
        )
        # "dynamics" keyword exists but D365 is not configured
        result = orch._select_agents("check dynamics orders")
        assert result == ["salesforce"]  # fallback: only SF is configured

    def test_multi_platform_task(self):
        orch = self._orch()
        result = orch._select_agents("Compare Salesforce pipeline with D365 opportunities")
        assert "salesforce" in result
        assert "dynamics365" in result


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

class TestRun:
    def test_run_dispatches_to_matched_agent(self):
        client = _mock_client()
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 result")
        orch._agents["salesforce"] = _mock_agent("SF result")

        results = orch.run("List all D365 orders")
        assert "dynamics365" in results
        assert results["dynamics365"] == "D365 result"

    def test_run_returns_all_when_no_keywords_match(self):
        client = _mock_client()
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 result")
        orch._agents["salesforce"] = _mock_agent("SF result")

        results = orch.run("What is the meaning of life?")
        assert set(results.keys()) == {"dynamics365", "salesforce"}

    def test_run_returns_dict_of_strings(self):
        orch = LivePlatformOrchestrator(azure_ai_config=_ai_config(), client=_mock_client())
        orch._agents["azure_ai"] = _mock_agent("AI answer")
        results = orch.run("Analyze this document")
        assert isinstance(results, dict)
        assert all(isinstance(v, str) for v in results.values())


# ---------------------------------------------------------------------------
# run_and_synthesize()
# ---------------------------------------------------------------------------

class TestRunAndSynthesize:
    def test_single_platform_returns_directly_no_extra_call(self):
        client = _mock_client("synthesized")
        orch = LivePlatformOrchestrator(salesforce_config=_sf_config(), client=client)
        orch._agents["salesforce"] = _mock_agent("SF response")

        result = orch.run_and_synthesize("Salesforce SOQL query")
        assert result == "SF response"
        # No synthesis call — only one platform
        client.messages.create.assert_not_called()

    def test_multi_platform_calls_synthesis(self):
        client = _mock_client("unified summary")
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 pipeline data")
        orch._agents["salesforce"] = _mock_agent("Salesforce pipeline data")

        result = orch.run_and_synthesize("Compare D365 and Salesforce pipeline")
        assert result == "unified summary"
        client.messages.create.assert_called_once()

    def test_synthesis_prompt_includes_platform_names(self):
        client = _mock_client("combined")
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 data")
        orch._agents["salesforce"] = _mock_agent("SF data")

        orch.run_and_synthesize("Compare D365 and Salesforce pipeline")
        call_kwargs = client.messages.create.call_args
        prompt = call_kwargs[1]["messages"][0]["content"]
        assert "DYNAMICS365" in prompt
        assert "SALESFORCE" in prompt

    def test_returns_string(self):
        client = _mock_client("answer")
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
        )
        orch._agents["dynamics365"] = _mock_agent("d")
        orch._agents["salesforce"] = _mock_agent("s")

        result = orch.run_and_synthesize("cross-platform report")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Circuit breaker integration
# ---------------------------------------------------------------------------

class TestCircuitBreakerIntegration:
    def _orch(self) -> LivePlatformOrchestrator:
        client = _mock_client()
        orch = LivePlatformOrchestrator(
            dynamics365_config=_d365_config(),
            salesforce_config=_sf_config(),
            client=client,
            breaker_failure_threshold=2,
            breaker_recovery_timeout=60.0,
        )
        orch._agents["dynamics365"] = _mock_agent("D365 ok")
        orch._agents["salesforce"] = _mock_agent("SF ok")
        return orch

    def test_platform_status_all_closed_initially(self):
        orch = self._orch()
        status = orch.platform_status
        assert all(v == "closed" for v in status.values())

    def test_successful_run_keeps_breakers_closed(self):
        orch = self._orch()
        orch.run("D365 orders")
        assert orch.platform_status["dynamics365"] == "closed"

    def test_agent_exception_recorded_against_breaker(self):
        orch = self._orch()
        orch._agents["dynamics365"] = _mock_agent()
        orch._agents["dynamics365"].run.side_effect = RuntimeError("timeout")

        result = orch.run("D365 orders")
        assert "[ERROR]" in result["dynamics365"]
        assert orch._breakers["dynamics365"].failure_count == 1

    def test_breaker_trips_after_threshold_failures(self):
        orch = self._orch()
        orch._agents["salesforce"].run.side_effect = RuntimeError("down")

        orch.run("Salesforce query")
        orch.run("Salesforce query")  # second failure trips breaker (threshold=2)
        assert orch.platform_status["salesforce"] == "open"

    def test_open_breaker_skipped_in_run(self):
        orch = self._orch()
        # Manually open the D365 breaker
        orch._breakers["dynamics365"].record_failure()
        orch._breakers["dynamics365"].record_failure()  # trips at threshold=2

        result = orch.run("D365 orders")
        assert "[UNAVAILABLE]" in result["dynamics365"]
        orch._agents["dynamics365"].run.assert_not_called()

    def test_open_breaker_skipped_in_run_async(self):
        import asyncio
        orch = self._orch()
        orch._breakers["salesforce"].record_failure()
        orch._breakers["salesforce"].record_failure()

        results = asyncio.run(orch.run_async("Salesforce SOQL"))
        assert "[UNAVAILABLE]" in results["salesforce"]
        orch._agents["salesforce"].run.assert_not_called()

    def test_breaker_resets_after_success(self):
        orch = self._orch()
        orch._agents["dynamics365"].run.side_effect = [RuntimeError("err"), "ok"]

        orch.run("D365 orders")                 # 1 failure
        assert orch._breakers["dynamics365"].failure_count == 1

        orch._agents["dynamics365"].run.side_effect = None
        orch._agents["dynamics365"].run.return_value = "ok"
        orch.run("D365 orders")                 # success
        assert orch._breakers["dynamics365"].failure_count == 0
        assert orch.platform_status["dynamics365"] == "closed"

    def test_manual_reset_reopens_tripped_breaker(self):
        orch = self._orch()
        orch._breakers["dynamics365"].record_failure()
        orch._breakers["dynamics365"].record_failure()  # OPEN
        assert orch.platform_status["dynamics365"] == "open"

        orch._breakers["dynamics365"].reset()
        assert orch.platform_status["dynamics365"] == "closed"
        assert orch._breakers["dynamics365"].is_available
