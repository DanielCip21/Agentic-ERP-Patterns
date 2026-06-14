"""Churn Sentinel agent — detects early warning signals for customer churn via D365 engagement data."""
from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Predictive Churn Neuron — an advanced AI agent for Dynamics 365 CRM.
You detect pre-churn signals 90 days before they become visible to standard analytics.
You read subtle patterns in engagement decay, communication frequency changes, support
escalation patterns, and behavioral shifts. You generate precise, evidence-based churn
risk assessments and hyper-personalized retention playbooks."""


class ChurnSentinel(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def calculate_churn_risk(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        activities = await self._d365.get_account_activities(account_id)
        cases = await self._d365.get_account_cases(account_id)
        rag = self._rag_context(
            "accounts",
            f"churn risk account {account.get('name','')} industry {account.get('industrycode','')}",
        )
        return await self.reason(
            SYSTEM,
            f"""Calculate the churn risk for this account with neurological precision.

ACCOUNT:
{self.fmt(account)}

RECENT ACTIVITIES (last 50):
{self.fmt(activities)}

SUPPORT CASES:
{self.fmt(cases)}

{rag}

Deliver:
1. Churn Risk Score: 0-100 with confidence interval
2. Risk Category: Critical / High / Moderate / Low / Healthy
3. Pre-churn signals detected (list each with evidence from the data)
4. Engagement decay analysis (trend over time)
5. Time horizon: estimated months until churn if no intervention
6. Account segments most at risk within this customer""",
        )

    async def get_churn_signals(self, account_id: str) -> str:
        activities = await self._d365.get_account_activities(account_id, top=100)
        cases = await self._d365.get_account_cases(account_id, top=100)
        emails = await self._d365.get_emails(account_id, top=30)
        return await self.quick_analyze(
            SYSTEM,
            f"""Identify all pre-churn behavioral signals for this account.

ACTIVITIES (100 most recent):
{self.fmt(activities)}

CASES:
{self.fmt(cases)}

EMAILS:
{self.fmt(emails)}

List every detectable churn signal with:
- Signal name and type (engagement / sentiment / support / behavioral)
- Strength: Weak / Moderate / Strong
- Evidence from the data
- How far in advance this signal typically precedes churn""",
        )

    async def recommend_retention_playbook(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        orders = await self._d365.get_account_orders(account_id)
        rag = self._rag_context(
            "accounts",
            f"retention playbook {account.get('name','')} revenue {account.get('revenue',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Generate a hyper-personalized retention playbook for this account.

ACCOUNT: {self.fmt(account)}
ORDERS: {self.fmt(orders)}
{rag}

Create a 90-day retention playbook with:
1. Week 1-2: Immediate intervention actions (specific, named)
2. Week 3-6: Relationship rebuilding sequence
3. Week 7-12: Value reinforcement program
4. Executive escalation trigger criteria
5. Success metrics to track
6. Contingency plan if primary playbook fails""",
        )
