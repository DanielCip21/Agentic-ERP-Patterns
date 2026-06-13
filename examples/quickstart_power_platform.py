"""Quickstart: Power Platform Agent — live API example.

Prerequisites
-------------
1. Register an Azure AD app with Power Automate and Dataverse permissions:
   - Power Automate: https://service.flow.microsoft.com/
   - Dataverse: Dynamics CRM > user_impersonation (or Application permission)

2. Add the app as a Dataverse application user with a security role:
   Power Platform admin center > Environments > Settings > Users > Application Users

3. Copy .env.example to .env and fill in your credentials:
   PP_ENVIRONMENT_ID=Default-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   PP_ENVIRONMENT_URL=https://yourorg.crm.dynamics.com
   PP_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   PP_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   PP_CLIENT_SECRET=your-secret
   ANTHROPIC_API_KEY=sk-ant-...

Run
---
    python examples/quickstart_power_platform.py
"""

import os
from dotenv import load_dotenv

from agentic_erp.connectors.power_platform import PowerPlatformConfig
from agentic_erp.api.power_platform_agent import PowerPlatformAgent

load_dotenv()


def main() -> None:
    config = PowerPlatformConfig(
        environment_id=os.environ["PP_ENVIRONMENT_ID"],
        environment_url=os.environ["PP_ENVIRONMENT_URL"],
        tenant_id=os.environ["PP_TENANT_ID"],
        client_id=os.environ["PP_CLIENT_ID"],
        client_secret=os.environ["PP_CLIENT_SECRET"],
    )

    agent = PowerPlatformAgent(config=config)

    print("=== Power Platform Agent ===\n")

    # Example 1: list flows
    response = agent.run(
        "List all Power Automate flows in this environment. How many are there?"
    )
    print("Flows:\n", response, "\n")

    # Example 2: query Dataverse
    response = agent.run(
        "Query the accounts table in Dataverse. Show the first 5 records with their names."
    )
    print("Accounts:\n", response, "\n")

    # Example 3 (mutating — uncomment and replace GUID to run):
    # response = agent.run(
    #     "Trigger flow 'YOUR-FLOW-GUID' with payload {\"order_id\": \"ORD-001\"}. "
    #     "Then check its run status."
    # )
    # print("Flow Trigger:\n", response)


if __name__ == "__main__":
    main()
