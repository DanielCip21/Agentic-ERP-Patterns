"""Relationship Mapper agent — builds stakeholder maps and influence networks from D365 contact data."""
from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Relationship Influence Graph — a specialized AI agent for Dynamics 365 CRM.
You map the hidden influence networks within every account to identify true economic buyers,
political champions, blockers, and decision paths. You discover relationship gaps — senior
contacts we've never engaged — and prescribe targeted multi-threading strategies to build
the relationships that actually close deals."""


class RelationshipMapper(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def map_stakeholder_influence(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        contacts = await self._d365.get_contacts(account_id)
        activities = await self._d365.get_account_activities(account_id, top=100)
        emails = await self._d365.get_emails(account_id, top=50)
        rag = self._rag_context(
            "accounts",
            f"stakeholder influence map enterprise account {account.get('name','')}",
        )
        return await self.reason(
            SYSTEM,
            f"""Map the complete stakeholder influence graph for this account.

ACCOUNT: {self.fmt(account)}
CONTACTS: {self.fmt(contacts)}
RECENT ACTIVITIES: {self.fmt(activities)}
EMAIL THREADS: {self.fmt(emails)}
{rag}

Deliver the Stakeholder Influence Graph:
1. Economic Buyer: Who controls the budget? (evidence-based)
2. Technical Buyer: Who evaluates and approves the solution?
3. User Buyers: Who will use and champion the solution?
4. Coach/Champion: Our internal advocate (if any)
5. Blockers: Who could kill the deal and why?
6. Influence Map: Who influences whom?
7. Engagement Coverage: Which key stakeholders are we NOT engaging?
8. Relationship Risk: Are we single-threaded (dangerously dependent on one contact)?""",
        )

    async def identify_decision_path(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        account_id = (opp.get("parentaccountid") or {}).get("accountid", "")
        contacts = await self._d365.get_contacts(account_id) if account_id else []
        rag = self._rag_context(
            "opportunities",
            f"decision path procurement buying committee {opp.get('estimatedvalue',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Map the decision path for this specific opportunity.

OPPORTUNITY: {self.fmt(opp)}
ACCOUNT CONTACTS: {self.fmt(contacts)}
{rag}

Map the Decision Path:
1. Decision stages (what approvals are required?)
2. Decision makers at each stage
3. Current stage in the buying process
4. Decision criteria at each gate
5. Estimated time for each stage
6. Bottlenecks: Where do deals like this typically stall?
7. Acceleration plays: How to compress the decision timeline""",
        )

    async def find_relationship_gaps(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        contacts = await self._d365.get_contacts(account_id)
        activities = await self._d365.get_account_activities(account_id, top=100)
        rag = self._rag_context(
            "accounts",
            f"relationship multi-threading executive engagement {account.get('name','')}",
        )
        return await self.quick_analyze(
            SYSTEM,
            f"""Identify relationship gaps in this account and prescribe coverage strategy.

ACCOUNT: {self.fmt(account)}
KNOWN CONTACTS: {self.fmt(contacts)}
RECENT ACTIVITIES: {self.fmt(activities)}
{rag}

Relationship Gap Analysis:
1. Coverage Gaps: Senior roles we've likely never engaged (by title/function)
2. Engagement Gaps: Contacts in our CRM we haven't touched in 90+ days
3. Influence Gaps: Key influencers not in our CRM at all
4. Multi-threading Score: How well are we covered? 1-10
5. Gap Closure Plan: Specific outreach plays for each gap (who reaches out, with what message)""",
        )
