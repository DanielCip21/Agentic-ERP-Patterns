# Architecture: Dynamics 365 Agentic RAG

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                MCP Client (Claude Desktop / Claude Code)        │
└───────────────────────────────┬────────────────────────────────┘
                               │ MCP Protocol (stdio)
┌───────────────────────────────▼──────────────────────────────────┐
│               FastMCP Server (mcp_server/server.py)             │
│               30 tools wired across 10 agent classes            │
└───────────────────────────────┬──────────────────────────────────┘
                               │
              ┌──────────────┴──────────────┐
              │                              │
┌─────────────▼───────┐ ┌─────────────▼───────┐
│  D365 Web API (OData v4)  │ │   ChromaDB RAG      │
│  MSAL OAuth2 token cache  │ │   Vector Store       │
│  Live real-time CRM data  │ │  - opportunities     │
└─────────────────────────┘ │  - accounts         │
              │              └─────────────────────┘
              │                      │
              └───────────┬──────────┘
                         │
               ┌─────────▼─────────┐
               │  Claude Opus 4.8    │
               │  Adaptive Thinking  │
               │  Streaming output   │
               └───────────────────┘
```

## Data Flow

1. **Tool call arrives** via MCP from Claude Desktop or another MCP client
2. **Agent fetches live data** from Dynamics 365 Web API using MSAL OAuth2 (client credentials flow)
3. **Agent queries RAG** — ChromaDB returns semantically similar historical CRM records
4. **Agent constructs prompt** combining live data + RAG context + a specialized system prompt
5. **Claude Opus 4.8 reasons** with adaptive thinking, streaming output back
6. **Result returns** through FastMCP to the MCP client

## RAG Collections

| Collection | Content | Indexed From |
|-----------|---------|-------------|
| `opportunities` | All opportunities: open, won, and lost | `rag/indexer.py` → D365 opportunities endpoint |
| `accounts` | All accounts | `rag/indexer.py` → D365 accounts endpoint |

The indexer must be run at least once before agents can return RAG-grounded analysis.
Schedule it to run nightly via cron or Azure Functions for fresh embeddings.

## Agent Design Principles

- **No guessing**: Every insight is grounded in live D365 data or RAG historical patterns
- **Adaptive thinking**: Claude reasons through complexity before generating the response  
- **Streaming**: All Claude calls stream to avoid timeouts on long, high-effort analyses
- **Async throughout**: All I/O (D365 API, ChromaDB, Anthropic API) is fully async Python
- **Tool granularity**: Each agent exposes 3 tools (focused tasks), not one monolith

## Tool Inventory (30 tools across 10 agents)

| Agent | Tools |
|-------|-------|
| Cognitive Deal DNA Profiler | `analyze_deal_dna`, `predict_deal_outcome`, `find_similar_deals` |
| Predictive Churn Neuron | `calculate_churn_risk`, `get_churn_signals`, `recommend_retention_playbook` |
| Revenue Genome Mapper | `map_revenue_genome`, `find_upsell_targets`, `calculate_wallet_share` |
| AI Contract Crystallizer | `analyze_contract_health`, `generate_negotiation_playbook`, `benchmark_deal_terms` |
| Living Account Health Index | `calculate_health_score`, `get_health_trend`, `trigger_health_intervention` |
| Adaptive Sales Neural Coach | `analyze_rep_performance`, `generate_coaching_plan`, `benchmark_against_top_performers` |
| Relationship Influence Graph | `map_stakeholder_influence`, `identify_decision_path`, `find_relationship_gaps` |
| Win/Loss Intelligence Engine | `analyze_win_loss_patterns`, `generate_battle_card`, `extract_winning_factors` |
| Deal Momentum Predictor | `predict_deal_momentum`, `identify_stalled_pipeline`, `optimize_rep_priorities` |
| 360° Voice Intelligence Synthesizer | `synthesize_customer_voice`, `analyze_sentiment_trend`, `generate_360_intelligence_report` |

## Security Notes

- MSAL acquires tokens via client credentials flow (Azure AD service principal)
- Tokens are cached in-process with a 60-second refresh buffer before expiry
- No CRM data persists outside ChromaDB (which runs locally under your control)
- `.env` is never committed — see `.gitignore` and `.env.example`
- D365 permissions should be scoped to the minimum required OData entities
