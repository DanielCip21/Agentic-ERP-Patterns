"""Quickstart: Dynamics 365 Order Agent — live API example.

Prerequisites
-------------
1. Create an App Registration in Azure AD:
   - Grant it the Dynamics 365 API permission:
     Dynamics CRM > user_impersonation (or use Application permission)
   - Create a client secret

2. In Dynamics 365 / Power Platform admin:
   - Add the app user: Settings > Users > Application Users
   - Assign a security role (e.g. Sales Manager)

3. Copy .env.example to .env and fill in your credentials:
   DYNAMICS_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   DYNAMICS_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   DYNAMICS_CLIENT_SECRET=your-client-secret
   DYNAMICS_ENVIRONMENT_URL=https://yourorg.crm.dynamics.com
   ANTHROPIC_API_KEY=sk-ant-...

Run
---
    python examples/quickstart_dynamics365.py
"""

import os
from dotenv import load_dotenv

from agentic_erp.connectors.dynamics365 import Dynamics365Config
from agentic_erp.erp.dynamics365_order_agent import Dynamics365OrderAgent

load_dotenv()


def main() -> None:
    config = Dynamics365Config(
        tenant_id=os.environ["DYNAMICS_TENANT_ID"],
        client_id=os.environ["DYNAMICS_CLIENT_ID"],
        client_secret=os.environ["DYNAMICS_CLIENT_SECRET"],
        environment_url=os.environ["DYNAMICS_ENVIRONMENT_URL"],
    )

    agent = Dynamics365OrderAgent(config=config)

    print("=== Dynamics 365 Order Agent ===\n")

    # Example 1: list active orders
    response = agent.run(
        "List all active sales orders (statecode eq 0). "
        "Summarise how many there are and the total value."
    )
    print("Active Orders:\n", response, "\n")

    # Example 2: specific order action
    # Replace with a real order GUID from your environment
    # response = agent.run(
    #     "Get order 00000000-0000-0000-0000-000000000001 and update its status to Submitted."
    # )
    # print("Order Update:\n", response)


if __name__ == "__main__":
    main()
