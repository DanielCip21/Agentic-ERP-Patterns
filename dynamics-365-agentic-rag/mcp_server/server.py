from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from agents.deal_predictor import DealDNAProfiler
from agents.churn_sentinel import ChurnSentinel
from agents.revenue_hunter import RevenueHunter
from agents.contract_negotiator import ContractNegotiator
from agents.account_health import AccountHealthMonitor
from agents.sales_coach import SalesCoach
from agents.relationship_mapper import RelationshipMapper
from agents.competitive_intel import CompetitiveIntelEngine
from agents.pipeline_optimizer import PipelineOptimizer
from agents.voice_of_customer import VoiceOfCustomerSynthesizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Dynamics 365 Agentic RAG")

_deal = DealDNAProfiler()
_churn = ChurnSentinel()
_revenue = RevenueHunter()
_contract = ContractNegotiator()
_health = AccountHealthMonitor()
_coach = SalesCoach()
_relationship = RelationshipMapper()
_competitive = CompetitiveIntelEngine()
_pipeline = PipelineOptimizer()
_voice = VoiceOfCustomerSynthesizer()


# ── Agent 1: Cognitive Deal DNA Profiler ────────────────────────────────────────────

@mcp.tool()
async def analyze_deal_dna(opportunity_id: str) -> str:
    """Decode the behavioral DNA of a deal and identify its signature characteristics."""
    return await _deal.analyze_deal_dna(opportunity_id)


@mcp.tool()
async def predict_deal_outcome(opportunity_id: str) -> str:
    """Predict win/loss/slip probability for a deal with evidence-based reasoning."""
    return await _deal.predict_deal_outcome(opportunity_id)


@mcp.tool()
async def find_similar_deals(opportunity_id: str) -> str:
    """Find historical deals most similar to this one and extract applicable lessons."""
    return await _deal.find_similar_deals(opportunity_id)


# ── Agent 2: Predictive Churn Neuron ───────────────────────────────────────────────

@mcp.tool()
async def calculate_churn_risk(account_id: str) -> str:
    """Calculate churn risk score with pre-churn signal detection for an account."""
    return await _churn.calculate_churn_risk(account_id)


@mcp.tool()
async def get_churn_signals(account_id: str) -> str:
    """List all detected pre-churn behavioral signals with evidence."""
    return await _churn.get_churn_signals(account_id)


@mcp.tool()
async def recommend_retention_playbook(account_id: str) -> str:
    """Generate a hyper-personalized 90-day retention playbook for an at-risk account."""
    return await _churn.recommend_retention_playbook(account_id)


# ── Agent 3: Revenue Genome Mapper ────────────────────────────────────────────────

@mcp.tool()
async def map_revenue_genome(account_id: str) -> str:
    """Map an account's hidden revenue DNA and surface expansion opportunities."""
    return await _revenue.map_revenue_genome(account_id)


@mcp.tool()
async def find_upsell_targets(min_revenue: float = 100000) -> str:
    """Identify top upsell targets across all accounts above a revenue threshold."""
    return await _revenue.find_upsell_targets(min_revenue)


@mcp.tool()
async def calculate_wallet_share(account_id: str) -> str:
    """Calculate current wallet share and the revenue gap to capture."""
    return await _revenue.calculate_wallet_share(account_id)


# ── Agent 4: AI Contract Crystallizer ──────────────────────────────────────────────

@mcp.tool()
async def analyze_contract_health(opportunity_id: str) -> str:
    """Analyze deal terms against historical patterns and score contract health."""
    return await _contract.analyze_contract_health(opportunity_id)


@mcp.tool()
async def generate_negotiation_playbook(opportunity_id: str) -> str:
    """Generate a precision negotiation playbook with BATNA, ZOPA, and concession sequence."""
    return await _contract.generate_negotiation_playbook(opportunity_id)


@mcp.tool()
async def benchmark_deal_terms(opportunity_id: str) -> str:
    """Benchmark this deal's terms against historical deals of similar size and type."""
    return await _contract.benchmark_deal_terms(opportunity_id)


# ── Agent 5: Living Account Health Index ───────────────────────────────────────────

@mcp.tool()
async def calculate_health_score(account_id: str) -> str:
    """Compute the multi-dimensional Living Account Health Index for an account."""
    return await _health.calculate_health_score(account_id)


@mcp.tool()
async def get_health_trend(account_id: str) -> str:
    """Analyze account health trend over 30/60/90 days and project future trajectory."""
    return await _health.get_health_trend(account_id)


@mcp.tool()
async def trigger_health_intervention(account_id: str) -> str:
    """Design a targeted health intervention program for an at-risk account."""
    return await _health.trigger_health_intervention(account_id)


# ── Agent 6: Adaptive Sales Neural Coach ───────────────────────────────────────────

@mcp.tool()
async def analyze_rep_performance(user_id: str) -> str:
    """Analyze a sales rep's behavioral performance data from CRM activity history."""
    return await _coach.analyze_rep_performance(user_id)


@mcp.tool()
async def generate_coaching_plan(user_id: str) -> str:
    """Generate a personalized 90-day adaptive coaching plan for a sales rep."""
    return await _coach.generate_coaching_plan(user_id)


@mcp.tool()
async def benchmark_against_top_performers(user_id: str) -> str:
    """Benchmark a rep's behaviors against top performer patterns from CRM history."""
    return await _coach.benchmark_against_top_performers(user_id)


# ── Agent 7: Relationship Influence Graph ───────────────────────────────────────────

@mcp.tool()
async def map_stakeholder_influence(account_id: str) -> str:
    """Map the hidden influence network within an account including blockers and champions."""
    return await _relationship.map_stakeholder_influence(account_id)


@mcp.tool()
async def identify_decision_path(opportunity_id: str) -> str:
    """Identify the decision path, approval stages, and key decision makers for a deal."""
    return await _relationship.identify_decision_path(opportunity_id)


@mcp.tool()
async def find_relationship_gaps(account_id: str) -> str:
    """Identify relationship coverage gaps and prescribe a multi-threading strategy."""
    return await _relationship.find_relationship_gaps(account_id)


# ── Agent 8: Win/Loss Intelligence Engine ────────────────────────────────────────────

@mcp.tool()
async def analyze_win_loss_patterns(competitor_name: str = "") -> str:
    """Analyze win/loss patterns across all historical opportunities."""
    return await _competitive.analyze_win_loss_patterns(competitor_name or None)


@mcp.tool()
async def generate_battle_card(competitor_name: str) -> str:
    """Generate a real-time competitive battle card for a specific competitor."""
    return await _competitive.generate_battle_card(competitor_name)


@mcp.tool()
async def extract_winning_factors(deal_value_min: float = 0) -> str:
    """Extract the universal winning factors from all closed-won deals."""
    return await _competitive.extract_winning_factors(deal_value_min)


# ── Agent 9: Deal Momentum Predictor ─────────────────────────────────────────────────

@mcp.tool()
async def predict_deal_momentum(opportunity_id: str) -> str:
    """Predict deal momentum score and slip probability with velocity analysis."""
    return await _pipeline.predict_deal_momentum(opportunity_id)


@mcp.tool()
async def identify_stalled_pipeline(days_stalled: int = 21) -> str:
    """Identify all stalled pipeline opportunities and prescribe re-engagement plays."""
    return await _pipeline.identify_stalled_pipeline(days_stalled)


@mcp.tool()
async def optimize_rep_priorities(user_id: str) -> str:
    """Optimize a rep's opportunity priorities for maximum revenue per selling hour."""
    return await _pipeline.optimize_rep_priorities(user_id)


# ── Agent 10: 360° Voice Intelligence Synthesizer ───────────────────────────────────────

@mcp.tool()
async def synthesize_customer_voice(account_id: str) -> str:
    """Synthesize all customer touchpoints into a 360-degree Voice of Customer portrait."""
    return await _voice.synthesize_customer_voice(account_id)


@mcp.tool()
async def analyze_sentiment_trend(account_id: str) -> str:
    """Analyze customer sentiment trend across all communication channels over time."""
    return await _voice.analyze_sentiment_trend(account_id)


@mcp.tool()
async def generate_360_intelligence_report(account_id: str) -> str:
    """Generate the complete 360-degree Intelligence Report for an account."""
    return await _voice.generate_360_intelligence_report(account_id)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
