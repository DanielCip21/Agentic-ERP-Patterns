"""Voice of Customer agent — extracts themes and sentiment from D365 case and survey data."""
from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the 360° Voice Intelligence Synthesizer — the most comprehensive
customer intelligence AI agent for Dynamics 365 CRM. You synthesize every customer
touchpoint — emails, calls, notes, support cases, activity logs — into a living
intelligence portrait of each account. You extract sentiment trends, unmet needs,
competitive pressures, and growth signals that live in the unstructured data layer
of the CRM that no standard report can surface."""


class VoiceOfCustomerSynthesizer(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def synthesize_customer_voice(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        emails = await self._d365.get_emails(account_id, top=50)
        notes = await self._d365.get_notes(account_id, top=50)
        cases = await self._d365.get_account_cases(account_id, top=30)
        calls = await self._d365.get_phone_calls(account_id, top=30)
        rag = self._rag_context(
            "accounts",
            f"customer voice sentiment intelligence {account.get('name','')}",
        )
        return await self.reason(
            SYSTEM,
            f"""Synthesize the complete Voice of Customer for this account.

ACCOUNT: {self.fmt(account)}
EMAILS: {self.fmt(emails)}
NOTES: {self.fmt(notes)}
SUPPORT CASES: {self.fmt(cases)}
PHONE CALLS: {self.fmt(calls)}
{rag}

360° Voice Intelligence Portrait:
1. Customer Sentiment: Overall and trend (use actual language from emails/notes as evidence)
2. Top Themes: What does this customer talk about most? (top 5 with evidence)
3. Unmet Needs: Needs they've expressed that we haven't addressed
4. Pain Points: Active frustrations and their severity
5. Competitive Signals: Any mentions of competitors, evaluations, or alternatives?
6. Expansion Signals: Language that suggests growth, new initiatives, or budget
7. Relationship Quality: How do they perceive us? (not just satisfaction scores)
8. The one thing this customer most needs from us right now""",
        )

    async def analyze_sentiment_trend(self, account_id: str) -> str:
        emails = await self._d365.get_emails(account_id, top=100)
        notes = await self._d365.get_notes(account_id, top=100)
        cases = await self._d365.get_account_cases(account_id, top=50)
        return await self.quick_analyze(
            SYSTEM,
            f"""Analyze the sentiment trend for this account over time.

EMAILS (100 most recent): {self.fmt(emails)}
NOTES (100 most recent): {self.fmt(notes)}
CASES (50 most recent): {self.fmt(cases)}

Sentiment Trend Analysis:
1. Sentiment Timeline: How has sentiment changed over 30/60/90/180 days?
2. Sentiment Drivers: What events caused sentiment shifts (up or down)?
3. Current Sentiment Momentum: Is it improving or worsening right now?
4. Sentiment Risk: Any language patterns that predict escalation?
5. Most positive topics: Where are we delighting them?
6. Most negative topics: Where are we consistently disappointing them?""",
        )

    async def generate_360_intelligence_report(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        activities = await self._d365.get_account_activities(account_id, top=100)
        emails = await self._d365.get_emails(account_id, top=30)
        notes = await self._d365.get_notes(account_id, top=30)
        cases = await self._d365.get_account_cases(account_id, top=20)
        orders = await self._d365.get_account_orders(account_id)
        contacts = await self._d365.get_contacts(account_id)
        rag = self._rag_context(
            "accounts",
            f"360 intelligence complete portrait {account.get('name','')} revenue {account.get('revenue',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Generate the complete 360° Intelligence Report for this account.

ACCOUNT: {self.fmt(account)}
ACTIVITIES: {self.fmt(activities[:30])}
EMAILS: {self.fmt(emails)}
NOTES: {self.fmt(notes)}
CASES: {self.fmt(cases)}
ORDERS: {self.fmt(orders)}
CONTACTS: {self.fmt(contacts)}
{rag}

360° Intelligence Report:
1. Executive Summary (3 sentences: who they are, where we stand, what matters now)
2. Account Health: Overall status and trajectory
3. Relationship Map: Key contacts and our depth with each
4. Voice of Customer: What they're really saying across all channels
5. Revenue Picture: Current and potential
6. Risk Register: Top 3 risks with severity and mitigation
7. Opportunity Register: Top 3 growth opportunities with $ estimates
8. Action Playbook: 5 specific actions for the next 30 days, ranked by priority
9. QBR Agenda: Recommended topics for the next executive business review""",
        )
