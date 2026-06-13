"""Pattern: Tool-use agent for HR — employee onboarding, access provisioning, compliance."""

from __future__ import annotations

from typing import Any

from agentic_erp.agents.base import BaseERPAgent
from agentic_erp.erp import hr_tools

_TOOLS = [
    {
        "name": "create_employee_record",
        "description": "Create a new employee record in the HRIS system to initiate onboarding.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Full name of the new employee"},
                "department": {"type": "string", "description": "Department (e.g. Engineering, Sales, Finance)"},
                "start_date": {"type": "string", "description": "Employment start date in YYYY-MM-DD format"},
            },
            "required": ["name", "department", "start_date"],
        },
    },
    {
        "name": "provision_system_access",
        "description": "Grant an employee access to the required internal systems.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "Employee ID"},
                "systems": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of systems to provision (e.g. ['ERP', 'CRM', 'VPN', 'Slack'])",
                },
            },
            "required": ["employee_id", "systems"],
        },
    },
    {
        "name": "assign_training",
        "description": "Assign role-appropriate training courses to a new employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "Employee ID"},
                "role": {"type": "string", "description": "Job role (e.g. engineer, sales, finance, manager)"},
            },
            "required": ["employee_id", "role"],
        },
    },
    {
        "name": "check_compliance_status",
        "description": "Check which compliance items (background check, I-9, NDA, etc.) are complete or pending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "Employee ID"},
            },
            "required": ["employee_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are an HR Onboarding Automation Agent for an enterprise organization.
Your responsibilities:
1. Create employee records when new hires are confirmed
2. Provision system access based on department and role requirements
3. Assign role-specific training curricula to ensure productivity from day one
4. Track and report compliance status — all items must be completed within 30 days

Ensure every new employee has system access and training assigned before their start date.
Flag incomplete compliance items immediately to the HR team."""


class HRAgent(BaseERPAgent):
    """Automates employee onboarding, system provisioning, and compliance tracking."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "create_employee_record":
                return hr_tools.create_employee_record(**inputs)
            case "provision_system_access":
                return hr_tools.provision_system_access(**inputs)
            case "assign_training":
                return hr_tools.assign_training(**inputs)
            case "check_compliance_status":
                return hr_tools.check_compliance_status(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
