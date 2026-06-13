"""Quickstart: Multi-Platform Orchestrator — unified cross-system queries.

Routes a natural-language task to the right live platform agent(s) and
optionally synthesizes a single answer with Claude.

Prerequisites
-------------
Configure any combination of platforms by setting the relevant env vars.
Only platforms with credentials configured will be used.

Dynamics 365 (optional):
    DYNAMICS_TENANT_ID, DYNAMICS_CLIENT_ID, DYNAMICS_CLIENT_SECRET,
    DYNAMICS_ENVIRONMENT_URL

Salesforce (optional):
    SF_INSTANCE_URL, SF_ACCESS_TOKEN

Power Platform (optional):
    PP_ENVIRONMENT_ID, PP_ENVIRONMENT_URL, PP_TENANT_ID,
    PP_CLIENT_ID, PP_CLIENT_SECRET

Azure AI (optional):
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT,
    AZURE_SEARCH_ENDPOINT (optional), AZURE_SEARCH_API_KEY (optional)

Dataverse (optional):
    DATAVERSE_ENVIRONMENT_URL, DATAVERSE_TENANT_ID,
    DATAVERSE_CLIENT_ID, DATAVERSE_CLIENT_SECRET

Always required:
    ANTHROPIC_API_KEY=sk-ant-...

Run
---
    python examples/quickstart_multi_platform.py
"""

import os
from dotenv import load_dotenv

from agentic_erp.connectors.azure_ai import AzureAIConfig
from agentic_erp.connectors.dataverse import DataverseConfig
from agentic_erp.connectors.dynamics365 import Dynamics365Config
from agentic_erp.connectors.power_platform import PowerPlatformConfig
from agentic_erp.connectors.salesforce import SalesforceConfig
from agentic_erp.patterns.live_platform_orchestrator import LivePlatformOrchestrator

load_dotenv()


def _load_configs() -> dict:
    """Build whichever platform configs have credentials in the environment."""
    configs = {}

    if all(os.getenv(k) for k in ("DYNAMICS_TENANT_ID", "DYNAMICS_CLIENT_ID",
                                   "DYNAMICS_CLIENT_SECRET", "DYNAMICS_ENVIRONMENT_URL")):
        configs["dynamics365_config"] = Dynamics365Config(
            tenant_id=os.environ["DYNAMICS_TENANT_ID"],
            client_id=os.environ["DYNAMICS_CLIENT_ID"],
            client_secret=os.environ["DYNAMICS_CLIENT_SECRET"],
            environment_url=os.environ["DYNAMICS_ENVIRONMENT_URL"],
        )

    if os.getenv("SF_INSTANCE_URL") and os.getenv("SF_ACCESS_TOKEN"):
        configs["salesforce_config"] = SalesforceConfig(
            instance_url=os.environ["SF_INSTANCE_URL"],
            access_token=os.environ["SF_ACCESS_TOKEN"],
        )

    if all(os.getenv(k) for k in ("PP_ENVIRONMENT_ID", "PP_ENVIRONMENT_URL",
                                   "PP_TENANT_ID", "PP_CLIENT_ID", "PP_CLIENT_SECRET")):
        configs["power_platform_config"] = PowerPlatformConfig(
            environment_id=os.environ["PP_ENVIRONMENT_ID"],
            environment_url=os.environ["PP_ENVIRONMENT_URL"],
            tenant_id=os.environ["PP_TENANT_ID"],
            client_id=os.environ["PP_CLIENT_ID"],
            client_secret=os.environ["PP_CLIENT_SECRET"],
        )

    if all(os.getenv(k) for k in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY",
                                   "AZURE_OPENAI_DEPLOYMENT")):
        configs["azure_ai_config"] = AzureAIConfig(
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT", ""),
            search_api_key=os.getenv("AZURE_SEARCH_API_KEY", ""),
        )

    if all(os.getenv(k) for k in ("DATAVERSE_ENVIRONMENT_URL", "DATAVERSE_TENANT_ID",
                                   "DATAVERSE_CLIENT_ID", "DATAVERSE_CLIENT_SECRET")):
        configs["dataverse_config"] = DataverseConfig(
            environment_url=os.environ["DATAVERSE_ENVIRONMENT_URL"],
            tenant_id=os.environ["DATAVERSE_TENANT_ID"],
            client_id=os.environ["DATAVERSE_CLIENT_ID"],
            client_secret=os.environ["DATAVERSE_CLIENT_SECRET"],
        )

    return configs


def main() -> None:
    configs = _load_configs()
    if not configs:
        print("No platform credentials found. Set at least one platform's env vars.")
        return

    orch = LivePlatformOrchestrator(**configs)
    print(f"=== Multi-Platform Orchestrator ===")
    print(f"Configured platforms: {', '.join(orch.configured_platforms)}\n")

    # Example 1: per-platform results
    results = orch.run(
        "List up to 5 open sales orders or opportunities. "
        "Show their names and values."
    )
    print("--- Per-platform results ---")
    for platform, response in results.items():
        print(f"\n[{platform.upper()}]\n{response}")

    # Example 2: synthesized cross-platform answer (only meaningful with 2+ platforms)
    if len(orch.configured_platforms) >= 2:
        print("\n--- Synthesized answer ---")
        answer = orch.run_and_synthesize(
            "Summarise the current sales pipeline health across all connected CRM platforms. "
            "Compare total open opportunity value and flag any gaps."
        )
        print(answer)


if __name__ == "__main__":
    main()
