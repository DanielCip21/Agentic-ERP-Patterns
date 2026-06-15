# Power Automate Custom Connector — Agentic ERP Patterns API

Register the ERP agent API as a Power Automate Custom Connector so any flow, Teams bot, or Copilot Studio topic can invoke AI agents without writing code.

## Prerequisites

- Azure subscription with an App Service or Container App running the API (`uvicorn agentic_erp.api.server:app --host 0.0.0.0 --port 8000`)
- Power Automate Premium licence (Custom Connectors require Premium)
- The `connector/openapi.json` file from this repository

---

## Step 1 — Deploy the API

Deploy the FastAPI server to Azure App Service (or any HTTPS endpoint):

```bash
# From the repository root
pip install -e "."
uvicorn agentic_erp.api.server:app --host 0.0.0.0 --port 8000
```

Set the `ANTHROPIC_API_KEY` environment variable in your App Service configuration before starting.

Note the public HTTPS URL, e.g. `https://dynavyx-erp-api.azurewebsites.net`.

---

## Step 2 — Create the Custom Connector

1. Go to **Power Automate** → **Data** → **Custom connectors**
2. Click **+ New custom connector** → **Import an OpenAPI file**
3. Name the connector `Agentic ERP Patterns`
4. Upload `connector/openapi.json` from this repository
5. Click **Continue**

---

## Step 3 — Configure the connector

On the **General** tab:
- **Host**: replace the placeholder with your actual deployment URL (e.g. `dynavyx-erp-api.azurewebsites.net`)
- **Base URL**: `/`
- **Scheme**: `HTTPS`

On the **Security** tab:
- Select **No authentication** for internal/dev use, or **API Key** for production
  - Header name: `X-API-Key`

On the **Definition** tab:
- Verify all 4 operations appear: `GetHealth`, `ListAgents`, `RunAgent`, `RunOrchestrator`

Click **Create connector**.

---

## Step 4 — Test the connector

1. Switch to the **Test** tab
2. Click **New connection** → **Create**
3. Select `RunAgent` → set `domain` = `order`, `task` = `"Get details for ORD-001"`
4. Click **Test operation** — you should receive a 200 response with `domain`, `result`, and `duration_ms`

---

## Step 5 — Use in a Power Automate flow

1. Create a new flow (e.g. **Automated cloud flow** triggered by a Teams message)
2. Add action → search for `Agentic ERP Patterns`
3. Select **RunAgent**
4. Map `domain` from a dropdown or dynamic content (e.g. `fixed_assets`)
5. Map `task` from the Teams message body
6. Add a **Reply in Teams** action with the `result` field from the connector response

---

## Step 6 — Use in Copilot Studio

1. Open Copilot Studio → your Copilot → **Actions**
2. Click **+ Add action** → **Power Automate flow**
3. Select the flow created in Step 5
4. Map inputs from topic variables to `domain` and `task`
5. Surface the `result` in the bot's response message

---

## Available Domains

| Domain | Description |
|--------|-------------|
| `order` | Order lifecycle: retrieve, verify inventory, update status |
| `inventory` | Stock replenishment: scan low-stock items, create POs |
| `fraud` | Transaction anomaly detection and risk scoring |
| `crypto` | Vendor payments via RippleNet (XRP) and Ethereum |
| `compliance` | Multi-jurisdiction tax and AML compliance |
| `cashflow` | Multi-currency cash flow forecasting |
| `vendor` | Vendor risk scoring and SLA-gated smart contract payments |
| `analytics` | Game revenue analytics and player cohort health |
| `fixed_assets` | Depreciation, disposal, revaluation, asset register |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 401 Unauthorized | Verify `ANTHROPIC_API_KEY` is set in App Service environment variables |
| 404 on agent domain | Use only the domain names listed in the table above |
| 422 Validation error | Ensure `task` field is non-empty in the request body |
| Timeout in Power Automate | Increase connector timeout to 120 s in connector settings (default 30 s is too short for LLM calls) |
