from __future__ import annotations

from agents.base_agent import BaseD365Agent
from d365.client import D365Client

SYSTEM = """You are the Revenue Genome Mapper — an elite AI agent for Dynamics 365 CRM.
You map every account's hidden revenue DNA, identifying latent upsell and cross-sell
opportunities that standard pipeline analysis cannot see. You analyze purchase patterns,
product gaps, wallet share, industry benchmarks, and growth signals to surface revenue
opportunities that sales reps have systematically overlooked."""


class RevenueHunter(BaseD365Agent):
    def __init__(self) -> None:
        super().__init__()
        self._d365 = D365Client()

    async def map_revenue_genome(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        orders = await self._d365.get_account_orders(account_id)
        opps = await self._d365.get_opportunities(top=50)
        account_opps = [
            o for o in opps
            if (o.get("parentaccountid") or {}).get("accountid") == account_id
        ]
        rag = self._rag_context(
            "accounts",
            f"revenue expansion account {account.get('name','')} revenue {account.get('revenue',0)} employees {account.get('numberofemployees',0)}",
        )
        return await self.reason(
            SYSTEM,
            f"""Map the complete revenue genome of this account.

ACCOUNT: {self.fmt(account)}
ORDERS: {self.fmt(orders)}
OPEN OPPORTUNITIES: {self.fmt(account_opps)}
{rag}

Deliver the Revenue Genome Map:
1. Current Revenue Footprint (what we have vs. what's possible)
2. Wallet Share Estimate (our % of their total spend in our category)
3. Expansion Chromosomes (5 specific upsell/cross-sell vectors with $ estimates)
4. Product Gap Analysis (what they buy elsewhere that we could own)
5. Revenue Sequencing (recommended order of expansion moves)
6. Total Addressable Revenue within this account (TAR)
7. 12-month revenue expansion roadmap""",
        )

    async def find_upsell_targets(self, min_revenue: float = 100000) -> str:
        accounts = await self._d365.get_accounts(top=300)
        targets = [a for a in accounts if float(a.get("revenue") or 0) >= min_revenue][:50]
        rag = self._rag_context("accounts", "upsell expansion high revenue accounts")
        return await self.reason(
            SYSTEM,
            f"""Identify the top upsell targets across all accounts.

CANDIDATE ACCOUNTS (filtered by min revenue ${min_revenue:,.0f}):
{self.fmt(targets)}

{rag}

Rank the top 10 upsell targets with:
1. Account name and why it's ranked here
2. Primary upsell vector (specific product/service)
3. Estimated incremental ARR
4. Ease of expansion: Easy / Medium / Hard
5. Recommended opening move
6. Time to revenue estimate""",
        )

    async def calculate_wallet_share(self, account_id: str) -> str:
        account = await self._d365.get_account(account_id)
        orders = await self._d365.get_account_orders(account_id)
        rag = self._rag_context(
            "accounts",
            f"wallet share industry {account.get('industrycode','')} employees {account.get('numberofemployees',0)}",
        )
        return await self.quick_analyze(
            SYSTEM,
            f"""Calculate our wallet share for this account and identify the gap.

ACCOUNT: {self.fmt(account)}
OUR ORDERS: {self.fmt(orders)}
{rag}

Provide:
1. Our total revenue from this account (from orders)
2. Estimated total addressable spend (based on their size and industry)
3. Wallet Share %: Current vs. Potential
4. Competitive displacement opportunity ($)
5. Specific budget areas we don't own yet""",
        )
