from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Cognitive Deal DNA Profiler — an elite AI agent for Dynamics 365 CRM.
Your purpose is to decode the unique behavioral DNA of every sales opportunity, identify hidden
risk and success patterns, and predict deal outcomes with precision. You analyze multi-dimensional
signals: deal velocity, engagement frequency, stakeholder dynamics, competitive pressure, and
historical analogs. Provide specific, actionable intelligence — not generic CRM commentary."""


class DealDNAProfiler(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def analyze_deal_dna(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        rag = self._rag_context(
            "opportunities",
            f"deal similar to {opp.get('name','')} value {opp.get('estimatedvalue',0)} probability {opp.get('closeprobability',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Analyze the DNA of this opportunity and identify its behavioral signature.

LIVE OPPORTUNITY DATA:
{self.fmt(opp)}

{rag}

Deliver:
1. Deal DNA Signature (5 defining characteristics)
2. Velocity Analysis (is this deal accelerating, stalling, or decaying?)
3. Risk Chromosomes (3 specific hidden risks not visible in the CRM fields)
4. Success Markers (what winning patterns from RAG history apply here?)
5. Probability Adjustment (your calibrated estimate vs. CRM's {opp.get('closeprobability','?')}%)
6. Next 3 actions ranked by impact on deal outcome""",
        )

    async def predict_deal_outcome(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        rag_won = self._rag_context("opportunities", f"won deal value {opp.get('estimatedvalue',0)}")
        rag_lost = self._rag_context("opportunities", f"lost deal probability {opp.get('closeprobability',0)}")
        return await self.reason(
            SYSTEM,
            f"""Predict the outcome of this deal with probabilistic precision.

DEAL DATA:
{self.fmt(opp)}

WON DEAL PATTERNS:
{rag_won}

LOST DEAL PATTERNS:
{rag_lost}

Provide:
1. Outcome Prediction: Win / Loss / Slip with confidence %
2. Primary win scenario and the conditions required
3. Primary loss scenario and the trigger that causes it
4. Time-to-close prediction vs. CRM close date
5. The single highest-leverage intervention to shift outcome""",
        )

    async def find_similar_deals(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        rag = self._rag_context(
            "opportunities",
            f"{opp.get('name','')} {opp.get('estimatedvalue',0)} {opp.get('closeprobability',0)}",
            k=12,
        )
        return await self.quick_analyze(
            SYSTEM,
            f"""Find the most similar historical deals to this opportunity and extract lessons.

TARGET DEAL: {self.fmt(opp)}

CANDIDATE HISTORICAL DEALS:
{rag}

For each similar deal found:
- Similarity score and why it matches
- What happened (won/lost/slipped)
- The decisive factor
- The lesson that applies to the target deal""",
        )
