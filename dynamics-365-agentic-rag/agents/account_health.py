from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Living Account Health Index — a continuous monitoring AI agent
for Dynamics 365 CRM. You compute multi-dimensional health scores for every account
by synthesizing engagement signals, support patterns, revenue trends, relationship
depth, and forward-looking risk indicators. You detect health degradation before
it becomes a retention problem and prescribe precise interventions."""


class AccountHealthMonitor(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def calculate_health_score(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        activities = await self._d365.get_account_activities(account_id, top=100)
        cases = await self._d365.get_account_cases(account_id, top=50)
        orders = await self._d365.get_account_orders(account_id)
        contacts = await self._d365.get_contacts(account_id)
        rag = self._rag_context(
            "accounts",
            f"health score engagement {account.get('name','')} revenue {account.get('revenue',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Compute the Living Account Health Index for this account.

ACCOUNT: {self.fmt(account)}
ACTIVITIES: {self.fmt(activities)}
CASES: {self.fmt(cases)}
ORDERS: {self.fmt(orders)}
CONTACTS: {self.fmt(contacts)}
{rag}

Deliver the Living Account Health Index:
1. Overall Health Score: 0-100 (color: Red/Amber/Green)
2. Health Dimensions (score each 0-100):
   - Engagement Health (activity frequency and quality)
   - Relationship Depth (contacts engaged, seniority)
   - Support Health (case volume, severity, resolution speed)
   - Revenue Health (order trend, growth, contract value)
   - Sentiment Health (communication tone signals)
3. Health Trend: Improving / Stable / Declining (with velocity)
4. Health Risks: Top 3 factors dragging the score down
5. Health Boosters: Top 3 factors you can act on immediately""",
        )

    async def get_health_trend(self, account_id: str) -> str:
        activities = await self._d365.get_account_activities(account_id, top=200)
        cases = await self._d365.get_account_cases(account_id, top=100)
        return await self.quick_analyze(
            SYSTEM,
            f"""Analyze the health trend for this account over time.

ACTIVITIES (200 most recent): {self.fmt(activities)}
CASES (100 most recent): {self.fmt(cases)}

Provide trend analysis:
1. Engagement trend: 30/60/90 day comparison
2. Support burden trend: Are cases increasing/decreasing?
3. Health trajectory: Where will this account be in 90 days if current trends continue?
4. Inflection points: Any sudden changes in engagement or support?
5. Leading vs. lagging indicators in this account's health""",
        )

    async def trigger_health_intervention(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        activities = await self._d365.get_account_activities(account_id, top=50)
        cases = await self._d365.get_account_cases(account_id, top=25)
        rag = self._rag_context(
            "accounts",
            f"health intervention recovery {account.get('name','')}",
        )
        return await self.reason(
            SYSTEM,
            f"""Design a health intervention program for this at-risk account.

ACCOUNT: {self.fmt(account)}
RECENT ACTIVITIES: {self.fmt(activities)}
OPEN CASES: {self.fmt(cases)}
{rag}

Design the intervention:
1. Intervention trigger: What specific signals require action now?
2. Intervention level: Tactical / Strategic / Executive
3. Immediate response (48 hours): Specific actions with owners
4. 30-day recovery plan with milestones
5. Success criteria: How do we know the intervention worked?
6. Escalation path if intervention fails""",
        )
