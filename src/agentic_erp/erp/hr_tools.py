"""Simulated HR backend — employee records, system access, training, compliance."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any

_EMPLOYEES: dict[str, dict] = {
    "EMP-001": {"id": "EMP-001", "name": "Alice Johnson", "department": "Engineering", "start_date": "2024-01-15", "status": "active"},
    "EMP-002": {"id": "EMP-002", "name": "Bob Martinez", "department": "Sales", "start_date": "2024-03-01", "status": "active"},
}

_SYSTEM_ACCESS: dict[str, list] = {}
_TRAINING_ASSIGNMENTS: dict[str, list] = {}

_ROLE_TRAINING_MAP = {
    "engineer": ["security_awareness", "code_review_standards", "cloud_architecture_101"],
    "sales": ["crm_mastery", "negotiation_skills", "product_training"],
    "finance": ["sox_compliance", "erp_finance_module", "expense_reporting"],
    "hr": ["hris_training", "data_privacy_gdpr", "performance_management"],
    "manager": ["leadership_fundamentals", "performance_reviews", "conflict_resolution"],
}

_COMPLIANCE_CHECKS = ["background_check", "i9_verification", "nda_signed", "code_of_conduct", "data_privacy_training"]


def create_employee_record(name: str, department: str, start_date: str) -> dict[str, Any]:
    emp_id = f"EMP-{random.randint(100, 999)}"
    record = {
        "id": emp_id,
        "name": name,
        "department": department,
        "start_date": start_date,
        "status": "onboarding",
        "email": f"{name.lower().replace(' ', '.')}@company.com",
        "created_at": datetime.utcnow().isoformat(),
    }
    _EMPLOYEES[emp_id] = record
    return record


def provision_system_access(employee_id: str, systems: list[str]) -> dict[str, Any]:
    if employee_id not in _EMPLOYEES:
        return {"error": f"Employee {employee_id} not found"}
    _SYSTEM_ACCESS[employee_id] = systems
    return {
        "employee_id": employee_id,
        "employee_name": _EMPLOYEES[employee_id]["name"],
        "systems_provisioned": systems,
        "access_granted_at": datetime.utcnow().isoformat(),
        "status": "provisioned",
    }


def assign_training(employee_id: str, role: str) -> dict[str, Any]:
    if employee_id not in _EMPLOYEES:
        return {"error": f"Employee {employee_id} not found"}
    role_lower = role.lower()
    courses = _ROLE_TRAINING_MAP.get(role_lower, ["general_onboarding", "security_awareness"])
    _TRAINING_ASSIGNMENTS[employee_id] = courses
    return {
        "employee_id": employee_id,
        "role": role,
        "courses_assigned": courses,
        "due_date": "30 days from start date",
        "status": "assigned",
    }


def check_compliance_status(employee_id: str) -> dict[str, Any]:
    if employee_id not in _EMPLOYEES:
        return {"error": f"Employee {employee_id} not found"}
    completed = random.sample(_COMPLIANCE_CHECKS, k=random.randint(2, len(_COMPLIANCE_CHECKS)))
    pending = [c for c in _COMPLIANCE_CHECKS if c not in completed]
    return {
        "employee_id": employee_id,
        "employee_name": _EMPLOYEES[employee_id]["name"],
        "completed_checks": completed,
        "pending_checks": pending,
        "compliance_percentage": round(len(completed) / len(_COMPLIANCE_CHECKS) * 100, 1),
        "status": "compliant" if not pending else "non_compliant",
        "checked_at": datetime.utcnow().isoformat(),
    }
