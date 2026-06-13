"""Pattern: Crypto payment orchestration agent (RippleNet / Ethereum smart contracts)."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import finance_tools

_TOOLS = [
    {
        "name": "initiate_crypto_payment",
        "description": "Create and submit a crypto payment to a vendor via RippleNet (XRP) or Ethereum (USDT/ETH).",
        "input_schema": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string", "description": "Target vendor ID"},
                "amount_usd": {"type": "number", "description": "Payment amount in USD equivalent"},
                "currency": {"type": "string", "description": "Crypto currency: USDT, ETH, or XRP", "enum": ["USDT", "ETH", "XRP"]},
            },
            "required": ["vendor_id", "amount_usd", "currency"],
        },
    },
    {
        "name": "get_crypto_payment",
        "description": "Retrieve the current status of a crypto payment by its payment ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string"},
            },
            "required": ["payment_id"],
        },
    },
    {
        "name": "confirm_payment_settlement",
        "description": "Confirm on-chain settlement of a crypto payment and update the AP ledger.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string"},
            },
            "required": ["payment_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Crypto Payment Orchestration Agent for a global gaming company.
You manage vendor payments via blockchain networks (RippleNet for XRP, Ethereum for USDT/ETH).
Your workflow:
1. Initiate the payment with the correct currency for the vendor/jurisdiction.
2. Retrieve payment status to confirm it is pending confirmation.
3. Confirm on-chain settlement once the blockchain transaction is ready.
4. Report the transaction hash and block confirmations as audit evidence.
Prefer XRP (RippleNet) for Asia-Pacific vendors (faster settlement). Use USDT for USD-denominated contracts.
Always confirm settlement before reporting a payment as complete."""


class CryptoPaymentAgent(BaseERPAgent):
    """Orchestrates vendor payments through RippleNet and Ethereum smart contracts."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "initiate_crypto_payment":
                return finance_tools.initiate_crypto_payment(**inputs)
            case "get_crypto_payment":
                return finance_tools.get_crypto_payment(**inputs)
            case "confirm_payment_settlement":
                return finance_tools.confirm_payment_settlement(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
