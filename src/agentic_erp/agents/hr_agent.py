"""Pattern: AI-powered HR & Payroll agent with multi-country compliance."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.tools import hr_tools

_TOOLS = [
    {
        "name": "analyze_skills_gap",
        "description": "Identify skills gaps for an employee vs their role requirements and generate training recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "Employee ID (e.g. EMP-001)"},
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "predict_attrition_risk",
        "description": "Predict the likelihood that an employee will leave the company using AI signals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
            },
            "required": ["employee_id"],
        },
    },
    {
        "name": "process_payroll",
        "description": "Process payroll for an employee for a given period with multi-country tax calculations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
                "period": {"type": "string", "description": "Payroll period in YYYY-MM format"},
            },
            "required": ["employee_id", "period"],
        },
    },
    {
        "name": "check_labor_law_compliance",
        "description": "Check an employee record for labor law compliance violations in their jurisdiction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
            },
            "required": ["employee_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are an AI-powered HR & Payroll Agent.
Your responsibilities:
- Identify skills gaps for each employee and recommend targeted training programs
- Predict employee attrition risk using behavioral and performance signals
- Process multi-country payroll with automated tax calculations
- Ensure compliance with local labor laws across all jurisdictions (US, EU, BR, etc.)
Always prioritize employee wellbeing alongside compliance and cost optimization.
Flag any HIGH-risk attrition or compliance violations for immediate manager review."""


class HRPayrollAgent(BaseERPAgent):
    """AI-driven HR: skills gap analysis, attrition prediction, payroll, labor compliance."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "analyze_skills_gap":
                return hr_tools.analyze_skills_gap(**inputs)
            case "predict_attrition_risk":
                return hr_tools.predict_attrition_risk(**inputs)
            case "process_payroll":
                return hr_tools.process_payroll(**inputs)
            case "check_labor_law_compliance":
                return hr_tools.check_labor_law_compliance(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
