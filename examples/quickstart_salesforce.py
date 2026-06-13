"""Quickstart: Salesforce CRM Agent — live API example.

Prerequisites
-------------
1. Create a Connected App in Salesforce Setup > App Manager:
   - Enable OAuth, select the "client_credentials" flow
   - Or use a pre-fetched session token (simpler for scripts)

2. Copy .env.example to .env and fill in your credentials:
   SF_INSTANCE_URL=https://yourorg.my.salesforce.com
   SF_ACCESS_TOKEN=00D...   # OR use SF_CLIENT_ID + SF_CLIENT_SECRET
   ANTHROPIC_API_KEY=sk-ant-...

Run
---
    python examples/quickstart_salesforce.py
"""

import os
from dotenv import load_dotenv

from agentic_erp.connectors.salesforce import SalesforceConfig
from agentic_erp.crm.salesforce_crm_agent import SalesforceCRMAgent

load_dotenv()


def main() -> None:
    # Option A — pre-fetched access token (simplest for scripts)
    config = SalesforceConfig(
        instance_url=os.environ["SF_INSTANCE_URL"],
        access_token=os.environ["SF_ACCESS_TOKEN"],
    )

    # Option B — Connected App OAuth2 (token managed automatically)
    # config = SalesforceConfig(
    #     instance_url=os.environ["SF_INSTANCE_URL"],
    #     client_id=os.environ["SF_CLIENT_ID"],
    #     client_secret=os.environ["SF_CLIENT_SECRET"],
    # )

    agent = SalesforceCRMAgent(config=config)

    print("=== Salesforce CRM Agent ===\n")

    # Example 1: recent leads
    response = agent.run(
        "Run a SOQL query to find the 5 most recently created Leads. "
        "List their names, companies, and status."
    )
    print("Recent Leads:\n", response, "\n")

    # Example 2: open pipeline
    response = agent.run(
        "Search for all Open opportunities with Amount greater than 10000. "
        "How many are there and what is the total pipeline value?"
    )
    print("Open Pipeline:\n", response, "\n")

    # Example 3 (mutating — uncomment to run):
    # response = agent.run(
    #     "Create a new Lead for Jane Doe at Acme Corp in the Technology industry."
    # )
    # print("New Lead:\n", response)


if __name__ == "__main__":
    main()
