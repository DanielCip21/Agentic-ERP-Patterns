"""Quickstart: Dataverse Agent — live API example.

Prerequisites
-------------
1. Register an Azure AD app with Dataverse permission:
   - Dynamics CRM > user_impersonation (delegated) or System User role (application)

2. Add the app as an application user in the Power Platform admin center:
   Environments > Settings > Users > Application Users > New app user

3. Copy .env.example to .env and fill in your credentials:
   DATAVERSE_ENVIRONMENT_URL=https://yourorg.crm.dynamics.com
   DATAVERSE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   DATAVERSE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   DATAVERSE_CLIENT_SECRET=your-secret
   ANTHROPIC_API_KEY=sk-ant-...

Run
---
    python examples/quickstart_dataverse.py
"""

import os
from dotenv import load_dotenv

from agentic_erp.connectors.dataverse import DataverseConfig
from agentic_erp.erp.dataverse_agent import DataverseAgent

load_dotenv()


def main() -> None:
    config = DataverseConfig(
        environment_url=os.environ["DATAVERSE_ENVIRONMENT_URL"],
        tenant_id=os.environ["DATAVERSE_TENANT_ID"],
        client_id=os.environ["DATAVERSE_CLIENT_ID"],
        client_secret=os.environ["DATAVERSE_CLIENT_SECRET"],
    )

    agent = DataverseAgent(config=config)

    print("=== Dataverse Agent ===\n")

    # Example 1: top accounts by revenue
    response = agent.run(
        "Query the accounts table. Show the top 5 accounts ordered by revenue descending. "
        "Include the name and revenue columns."
    )
    print("Top Accounts:\n", response, "\n")

    # Example 2: count active leads
    response = agent.run(
        "Count how many active leads (statecode eq 0) are in the system."
    )
    print("Active Lead Count:\n", response, "\n")

    # Example 3 (FetchXML — uncomment to run):
    # response = agent.run(
    #     "Run a FetchXML report on accounts joined to their primary contacts. "
    #     "Show account name and contact email."
    # )
    # print("FetchXML Report:\n", response)


if __name__ == "__main__":
    main()
