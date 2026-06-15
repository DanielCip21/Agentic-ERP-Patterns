"""Pattern: Human-in-the-loop agent for high-value ERP actions.

The agent runs its tool-use loop normally but pauses and requests human approval
before executing any tool that exceeds a configurable value threshold.
"""

from __future__ import annotations

import json
from typing import Any, Callable


from agentic_erp.agents.order_agent import OrderProcessingAgent

# Actions requiring human approval and their value extractor functions.
_HIGH_VALUE_TOOLS = {
    "update_order_status": lambda inputs: (
        inputs.get("status") in {"shipped", "cancelled"}
    ),
    "create_purchase_order": lambda inputs: inputs.get("quantity", 0) > 50,
}


class HumanInLoopAgent(OrderProcessingAgent):
    """Extends OrderProcessingAgent to gate high-value tool calls on human approval.

    Provide an `approval_callback` to integrate with your approval system
    (Slack, Teams Adaptive Card, Power Automate flow, etc.).
    Default callback prompts via stdin — useful for local development.
    """

    def __init__(
        self,
        approval_callback: Callable[[str, dict], bool] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._approval_callback = approval_callback or self._stdin_approval

    def run(self, user_message: str) -> str:
        messages: list[dict] = [{"role": "user", "content": user_message}]

        for _ in range(self.MAX_ITERATIONS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                return ""

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    gated = _HIGH_VALUE_TOOLS.get(block.name)
                    if gated and gated(block.input):
                        approved = self._approval_callback(block.name, block.input)
                        if not approved:
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps(
                                        {"error": "Action rejected by human reviewer."}
                                    ),
                                }
                            )
                            continue

                    result = self._dispatch_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

        raise RuntimeError("Agent exceeded maximum iterations.")

    @staticmethod
    def _stdin_approval(tool_name: str, inputs: dict[str, Any]) -> bool:
        print(f"\n[APPROVAL REQUIRED] Tool: {tool_name}")
        print(f"Inputs: {json.dumps(inputs, indent=2)}")
        answer = input("Approve? (y/n): ").strip().lower()
        return answer == "y"
