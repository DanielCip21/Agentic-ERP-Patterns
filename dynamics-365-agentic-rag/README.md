# Dynamics 365 Agentic RAG — 10 AI Agents for CRM Intelligence

> 10 production-grade Agentic RAG MCP AI agents purpose-built for Microsoft Dynamics 365 CRM. Each agent combines real-time D365 data retrieval, semantic vector search over historical CRM knowledge, and Claude Opus 4.8's adaptive reasoning to deliver intelligence that no off-the-shelf CRM tool provides today.

## Agents

| # | Agent | What It Does |
|---|-------|-------------|
| 1 | **Cognitive Deal DNA Profiler** | Decodes the unique behavioral signature of every deal and predicts outcome probability using multi-dimensional historical pattern matching |
| 2 | **Predictive Churn Neuron** | Detects pre-churn signals 90 days before they become visible to humans using subtle engagement decay patterns |
| 3 | **Revenue Genome Mapper** | Maps every account's hidden revenue DNA to surface upsell and cross-sell opportunities invisible to standard pipeline views |
| 4 | **AI Contract Crystallizer** | Analyzes deal terms against historical win/loss data to recommend optimal negotiation positions in real time |
| 5 | **Living Account Health Index** | Computes a continuously updating, multi-signal health score per account and triggers interventions before health degrades |
| 6 | **Adaptive Sales Neural Coach** | Provides personalized, data-driven coaching for each sales rep based on their unique behavioral patterns vs. top performers |
| 7 | **Relationship Influence Graph** | Discovers the hidden influence network within every account to identify true economic buyers and decision paths |
| 8 | **Win/Loss Intelligence Engine** | Extracts deep competitive intelligence from every won and lost deal to generate dynamic battle cards |
| 9 | **Deal Momentum Predictor** | Quantifies deal velocity and momentum decay to predict which deals will slip and which will close early |
| 10 | **360° Voice Intelligence Synthesizer** | Synthesizes every customer touchpoint — emails, calls, notes, cases — into a living intelligence portrait |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server (FastMCP)                  │
│              Exposes 30 tools across 10 agents           │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼──────────┐         ┌─────────▼────────┐
│  Dynamics 365    │         │   ChromaDB RAG    │
│  Web API (OData) │         │   Vector Store    │
│  Live CRM Data   │         │ Historical Patterns│
└──────────────────┘         └──────────────────┘
        │                               │
        └───────────────┬───────────────┘
                        │
              ┌─────────▼──────────┐
              │  Claude Opus 4.8   │
              │  Adaptive Thinking │
              │  Agentic Reasoning │
              └────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Microsoft Dynamics 365 instance with API access
- Anthropic API key
- Azure AD app registration with D365 permissions

### Installation

```bash
git clone <this-repo>
cd dynamics-365-agentic-rag
pip install -e .
cp .env.example .env
# Fill in your credentials in .env
```

### Index your D365 data into the RAG store

```bash
python -m rag.indexer
```

### Start the MCP server

```bash
python -m mcp_server.server
```

### Connect from Claude Desktop

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "dynamics365-rag": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "D365_TENANT_ID": "...",
        "D365_CLIENT_ID": "...",
        "D365_CLIENT_SECRET": "...",
        "D365_BASE_URL": "https://yourorg.crm.dynamics.com"
      }
    }
  }
}
```

## Configuration

All configuration is via environment variables (see `.env.example`).

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `ANTHROPIC_MODEL` | Model ID (default: `claude-opus-4-8`) |
| `D365_TENANT_ID` | Azure AD tenant ID |
| `D365_CLIENT_ID` | Azure AD app client ID |
| `D365_CLIENT_SECRET` | Azure AD app client secret |
| `D365_BASE_URL` | D365 base URL, e.g. `https://org.crm.dynamics.com` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB persistence path (default: `./chroma_db`) |
| `MCP_HOST` | MCP server host (default: `0.0.0.0`) |
| `MCP_PORT` | MCP server port (default: `8000`) |

## License

MIT
