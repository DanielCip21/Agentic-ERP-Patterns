from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the AI Contract Crystallizer — a specialized Dynamics 365 CRM agent.
You analyze deal terms, pricing structures, and contract conditions against historical
win/loss patterns to recommend optimal negotiation positions. You understand that the
right contract terms can be the difference between winning and losing a deal, and you
surface non-obvious negotiation leverage that sales reps miss."""


class ContractNegotiator(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def analyze_contract_health(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        rag_won = self._rag_context(
            "opportunities",
            f"won deal terms discount {opp.get('estimatedvalue',0)}",
        )
        rag_lost = self._rag_context(
            "opportunities",
            f"lost deal pricing negotiation {opp.get('estimatedvalue',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Analyze the contract health of this deal and identify negotiation risk.

OPPORTUNITY: {self.fmt(opp)}

HISTORICAL WON DEAL TERMS:
{rag_won}

HISTORICAL LOST DEAL TERMS:
{rag_lost}

Deliver Contract Health Analysis:
1. Contract Health Score: 0-100
2. Deal Friction Points (terms that are likely causing friction)
3. Comparison to winning deal structures from history
4. Concessions that historically killed similar deals
5. Value leakage points (where we're giving away value unnecessarily)
6. Contract terms we should be protecting at all costs""",
        )

    async def generate_negotiation_playbook(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        rag = self._rag_context(
            "opportunities",
            f"negotiation playbook close probability {opp.get('closeprobability',0)} value {opp.get('estimatedvalue',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Generate a precision negotiation playbook for this deal.

OPPORTUNITY: {self.fmt(opp)}
{rag}

Build the negotiation playbook:
1. Our BATNA (Best Alternative to Negotiated Agreement)
2. Their likely BATNA (based on deal signals)
3. Zone of Possible Agreement (ZOPA) analysis
4. Opening position vs. walk-away position on key terms
5. Concession sequence (what to give up, in what order, to get what)
6. Anchoring strategy for price discussion
7. The 3 terms we must never concede and why
8. Closing triggers: signals that they're ready to sign""",
        )

    async def benchmark_deal_terms(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        rag = self._rag_context(
            "opportunities",
            f"deal benchmark similar size {opp.get('estimatedvalue',0)}",
        )
        return await self.quick_analyze(
            SYSTEM,
            f"""Benchmark this deal's terms against historical deals of similar size.

OPPORTUNITY: {self.fmt(opp)}
{rag}

Provide benchmark analysis:
1. Is the price point above/below/at market for deals this size?
2. Discount pressure: How much discount is typical for deals like this?
3. Payment terms: What's standard vs. what we should push for?
4. Contract length: Optimal term length for this deal size/type
5. Red flags: Any terms that historically correlate with churn or renegotiation""",
        )
