"""Competitive Intelligence agent — surfaces competitor insights from D365 opportunity and win/loss data."""
from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Win/Loss Intelligence Engine — a competitive intelligence AI agent
for Dynamics 365 CRM. You extract deep competitive patterns from every won and lost deal,
generate real-time battle cards, and identify the factors that consistently win or lose
deals against specific competitors. You turn historical CRM data into a continuously
evolving competitive advantage."""


class CompetitiveIntelEngine(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def analyze_win_loss_patterns(self, competitor_name: str | None = None) -> str:
        won = await self._d365.get_won_opportunities(top=500)
        lost = await self._d365.get_lost_opportunities(top=500)
        query = f"competitive intelligence {competitor_name or 'all competitors'} win loss"
        rag = self._rag_context("opportunities", query, k=12)
        return await self.reason(
            SYSTEM,
            f"""Analyze comprehensive win/loss patterns{' against ' + competitor_name if competitor_name else ''}.

WON OPPORTUNITIES ({len(won)} total):
{self.fmt(won[:20])}
... (showing first 20 of {len(won)})

LOST OPPORTUNITIES ({len(lost)} total):
{self.fmt(lost[:20])}
... (showing first 20 of {len(lost)})

{rag}

Win/Loss Intelligence Report:
1. Overall Win Rate and trend
2. Win patterns: What do all wins have in common? (top 5 factors)
3. Loss patterns: What do all losses have in common? (top 5 factors)
4. Competitive displacement: Where are we winning vs. losing market share?
5. Deal size analysis: Win rate by deal size band
6. Timing patterns: How does time-in-stage affect win rate?
7. Top 3 things we must stop doing to win more deals
8. Top 3 things we must start doing""",
        )

    async def generate_battle_card(self, competitor_name: str) -> str:
        won = await self._d365.get_won_opportunities(top=300)
        lost = await self._d365.get_lost_opportunities(top=300)
        rag = self._rag_context(
            "opportunities",
            f"competitive battle card {competitor_name} win loss",
        )
        return await self.reason(
            SYSTEM,
            f"""Generate a real-time battle card for competing against {competitor_name}.

HISTORICAL WIN/LOSS DATA:
WON: {self.fmt(won[:15])}
LOST: {self.fmt(lost[:15])}

{rag}

Battle Card for {competitor_name}:
1. Where we consistently beat {competitor_name} (our proof points)
2. Where {competitor_name} beats us (and how to neutralize it)
3. Their typical FUD (Fear, Uncertainty, Doubt) tactics and our rebuttals
4. Our killer differentiators (with proof from won deals)
5. Trap questions to disqualify them early in the deal
6. Landmines to plant: Questions that expose their weaknesses
7. Testimonials / case study angles that win against this competitor
8. Pricing/discount patterns when we face {competitor_name}""",
        )

    async def extract_winning_factors(self, deal_value_min: float = 0) -> str:
        won = await self._d365.get_won_opportunities(top=500)
        filtered = [o for o in won if float(o.get("estimatedvalue") or 0) >= deal_value_min]
        rag = self._rag_context(
            "opportunities",
            f"winning factors success patterns deals above {deal_value_min}",
        )
        return await self.quick_analyze(
            SYSTEM,
            f"""Extract the universal winning factors from all closed-won deals >= ${deal_value_min:,.0f}.

WON DEALS ({len(filtered)} filtered):
{self.fmt(filtered[:25])}

{rag}

Winning Factor Analysis:
1. Top 10 factors that appear in nearly every won deal
2. Surprise factors (factors that correlate with winning but aren't obvious)
3. The critical path to a win: What must happen, in what order?
4. Anti-patterns: Things that seem good but correlate with losing
5. The single most predictive factor of winning a deal""",
        )
