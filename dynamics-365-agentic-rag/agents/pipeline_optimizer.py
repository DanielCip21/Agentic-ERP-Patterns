"""Pipeline Optimizer agent — identifies pipeline bottlenecks and recommends stage-progression actions."""
from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Deal Momentum Predictor — a pipeline intelligence AI agent for
Dynamics 365 CRM. You quantify deal velocity and momentum across every opportunity in
the pipeline, identify momentum decay before deals slip, and optimize rep priorities
to maximize revenue per hour of selling time. You see the pipeline as a fluid, dynamic
system where momentum — not just probability — determines outcomes."""


class PipelineOptimizer(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def predict_deal_momentum(self, opportunity_id: str) -> str:
        opp = await self._d365.get_opportunity(opportunity_id)
        account_id = (opp.get("parentaccountid") or {}).get("accountid", "")
        activities = await self._d365.get_account_activities(account_id, top=50) if account_id else []
        rag = self._rag_context(
            "opportunities",
            f"deal momentum velocity close probability {opp.get('closeprobability',0)} value {opp.get('estimatedvalue',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Predict the deal momentum for this opportunity.

OPPORTUNITY: {self.fmt(opp)}
RECENT ACCOUNT ACTIVITIES: {self.fmt(activities)}
{rag}

Deal Momentum Report:
1. Momentum Score: -100 (decelerating) to +100 (accelerating)
2. Velocity: Days per stage vs. historical average for this deal size
3. Momentum drivers: What's propelling this deal forward?
4. Momentum killers: What's creating drag?
5. Slip probability: % chance this deal misses the current close date
6. Predicted actual close date (momentum-adjusted)
7. The single intervention that would have the highest momentum impact""",
        )

    async def identify_stalled_pipeline(self, days_stalled: int = 21) -> str:
        opps = await self._d365.get_opportunities(top=500)
        rag = self._rag_context(
            "opportunities",
            f"stalled deals pipeline stuck inactive {days_stalled} days",
        )
        return await self.reason(
            SYSTEM,
            f"""Identify all stalled deals in the pipeline (inactive for {days_stalled}+ days).

ALL OPEN OPPORTUNITIES:
{self.fmt(opps)}

{rag}

Stalled Pipeline Analysis:
1. Stalled deal list (ranked by risk-adjusted revenue at stake)
2. For each stalled deal:
   - Days since last activity
   - Estimated slip risk: High / Medium / Low
   - Most likely reason for stall (data-driven)
   - Specific re-engagement play to restart momentum
3. Total revenue at risk from stalled pipeline
4. Priority-ordered action list for this week
5. Root cause patterns: Why are deals stalling at these stages?""",
        )

    async def optimize_rep_priorities(self, user_id: str) -> str:
        activities = await self._d365.get_user_activities(user_id, top=100)
        opps = await self._d365.get_opportunities(top=200)
        rag = self._rag_context("opportunities", "rep priority optimization high impact opportunities")
        return await self.reason(
            SYSTEM,
            f"""Optimize this rep's opportunity priorities for maximum revenue impact.

REP ACTIVITIES (recent): {self.fmt(activities)}
ALL OPEN OPPORTUNITIES: {self.fmt(opps[:30])}
{rag}

Priority Optimization Plan:
1. Tier 1 (Close This Week): Opportunities with momentum to close now
2. Tier 2 (Nurture Actively): High-value deals needing attention
3. Tier 3 (Monitor): Deals that need time but shouldn't be neglected
4. Tier 4 (Deprioritize or Disqualify): Deals draining time without ROI
5. Recommended daily activity allocation (% time per tier)
6. Specific next action for each Tier 1 and 2 deal""",
        )
