"""Sales Coach agent — analyses rep activity in D365 and delivers personalised coaching recommendations."""
from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Adaptive Sales Neural Coach — an AI agent for Dynamics 365 CRM.
You provide hyper-personalized, data-driven coaching for individual sales reps based
on their unique behavioral patterns, strengths, gaps, and comparison to top performers.
You don't give generic sales advice — you analyze actual CRM behavior data and prescribe
specific, measurable behavioral changes that will move the rep's performance metrics."""


class SalesCoach(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def analyze_rep_performance(self, user_id: str) -> str:
        activities = await self._d365.get_user_activities(user_id, top=200)
        rag = self._rag_context("opportunities", "sales rep performance activity patterns")
        return await self.reason(
            SYSTEM,
            f"""Analyze this sales rep's performance based on their behavioral data.

REP ACTIVITIES (200 most recent): {self.fmt(activities)}
{rag}

Deliver the Performance Analysis:
1. Activity Score: Volume, type distribution, and quality signals
2. Behavioral Patterns: What this rep actually does vs. what top performers do
3. Strengths: Where this rep's behavior correlates with winning
4. Gaps: Specific behavioral deficits with evidence from the data
5. Win Rate Drivers: Activities that most predict this rep's wins
6. Pipeline Management Quality: Are they working the right opportunities?
7. Time Allocation Analysis: Where is their time going vs. where it should go?""",
        )

    async def generate_coaching_plan(self, user_id: str) -> str:
        activities = await self._d365.get_user_activities(user_id, top=200)
        rag = self._rag_context("opportunities", "top performer coaching behavioral patterns")
        return await self.reason(
            SYSTEM,
            f"""Generate a personalized 90-day neural coaching plan for this rep.

REP ACTIVITIES: {self.fmt(activities)}
{rag}

Build the Adaptive Coaching Plan:
1. Rep Archetype (based on behavioral data): Hunter / Farmer / Consultant / Relationship Builder
2. Development Priority Stack (top 3 skills to develop, ranked by impact)
3. Weekly Behavioral Targets (specific, measurable activity changes)
4. 30-60-90 Day Milestones with specific metrics
5. Manager coaching touchpoints: What to observe and reinforce
6. Rep self-assessment exercises (behavioral experiments to run)
7. Success metrics: How we'll measure coaching effectiveness""",
        )

    async def benchmark_against_top_performers(self, user_id: str) -> str:
        activities = await self._d365.get_user_activities(user_id, top=200)
        rag = self._rag_context("opportunities", "top performer high win rate behaviors patterns")
        return await self.quick_analyze(
            SYSTEM,
            f"""Benchmark this rep's behaviors against top performers in the CRM history.

REP ACTIVITIES: {self.fmt(activities)}

TOP PERFORMER PATTERNS FROM RAG:
{rag}

Provide the benchmark gap analysis:
1. Top Performer Profile (synthesized from RAG patterns)
2. This Rep vs. Top Performer: Side-by-side on 8 key behavioral dimensions
3. Biggest performance gaps (ranked by impact on revenue)
4. Quickest wins: Behavioral changes that would have immediate pipeline impact
5. Structural advantages this rep has that are underutilized""",
        )
