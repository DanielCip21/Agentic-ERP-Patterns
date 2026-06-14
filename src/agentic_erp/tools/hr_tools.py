"""Simulated HR & Payroll tools."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any


_EMPLOYEES: dict[str, dict] = {
    "EMP-001": {"id": "EMP-001", "name": "Alice Chen", "department": "Finance", "role": "Financial Analyst", "salary": 92000.00, "country": "US", "tenure_years": 4.5, "performance_score": 88},
    "EMP-002": {"id": "EMP-002", "name": "Bob Kumar", "department": "IT", "role": "D365 Developer", "salary": 115000.00, "country": "US", "tenure_years": 2.1, "performance_score": 76},
    "EMP-003": {"id": "EMP-003", "name": "Clara Silva", "department": "Operations", "role": "Supply Chain Manager", "salary": 105000.00, "country": "BR", "tenure_years": 6.3, "performance_score": 93},
}

_REQUIRED_SKILLS: dict[str, list[str]] = {
    "Finance": ["D365 Finance", "Power BI", "IFRS", "FP&A", "Power Automate"],
    "IT": ["D365 CE", "Azure", "Power Platform", "CI/CD", "Python"],
    "Operations": ["D365 SCM", "Power BI", "Lean Manufacturing", "IoT", "SAP"],
}

_EMPLOYEE_SKILLS: dict[str, list[str]] = {
    "EMP-001": ["D365 Finance", "Power BI", "IFRS"],
    "EMP-002": ["D365 CE", "Azure"],
    "EMP-003": ["D365 SCM", "Power BI", "Lean Manufacturing", "IoT"],
}

_PAYROLL_RUNS: list[dict] = []

_TAX_RATES: dict[str, dict] = {
    "US": {"federal": 0.22, "state": 0.05, "social_security": 0.062, "medicare": 0.0145},
    "BR": {"federal": 0.275, "social_security": 0.09},
    "DE": {"federal": 0.42, "social_security": 0.2025},
}


def analyze_skills_gap(employee_id: str) -> dict[str, Any]:
    employee = _EMPLOYEES.get(employee_id)
    if not employee:
        return {"error": f"Employee {employee_id} not found"}
    required = _REQUIRED_SKILLS.get(employee["department"], [])
    current = _EMPLOYEE_SKILLS.get(employee_id, [])
    missing = [s for s in required if s not in current]
    coverage = round(len(current) / len(required) * 100, 1) if required else 100.0
    return {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "department": employee["department"],
        "required_skills": required,
        "current_skills": current,
        "missing_skills": missing,
        "skill_coverage_pct": coverage,
        "training_priority": "HIGH" if coverage < 60 else "MEDIUM" if coverage < 80 else "LOW",
        "recommended_courses": [f"{s} Certification" for s in missing],
    }


def predict_attrition_risk(employee_id: str) -> dict[str, Any]:
    employee = _EMPLOYEES.get(employee_id)
    if not employee:
        return {"error": f"Employee {employee_id} not found"}
    score = 0
    factors = []
    if employee["performance_score"] < 80:
        score += 20
        factors.append("Below-average performance score")
    if employee["tenure_years"] < 2:
        score += 25
        factors.append("Short tenure (high early attrition risk)")
    if employee["tenure_years"] > 5 and employee["performance_score"] > 88:
        score += 15
        factors.append("Senior high-performer — retention risk if not promoted")
    gap = analyze_skills_gap(employee_id)
    if gap.get("training_priority") == "HIGH":
        score += 20
        factors.append("Significant skills gap with no development plan")
    return {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "attrition_risk_score": min(100, score),
        "risk_level": "HIGH" if score >= 50 else "MEDIUM" if score >= 25 else "LOW",
        "contributing_factors": factors,
        "recommended_actions": ["Schedule retention conversation", "Review compensation"] if score >= 50 else ["Annual check-in"],
    }


def process_payroll(employee_id: str, period: str) -> dict[str, Any]:
    employee = _EMPLOYEES.get(employee_id)
    if not employee:
        return {"error": f"Employee {employee_id} not found"}
    monthly_gross = employee["salary"] / 12
    tax_config = _TAX_RATES.get(employee["country"], _TAX_RATES["US"])
    total_tax_rate = sum(tax_config.values())
    net_pay = round(monthly_gross * (1 - total_tax_rate), 2)
    total_deductions = round(monthly_gross - net_pay, 2)
    payrun = {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "period": period,
        "country": employee["country"],
        "gross_pay": round(monthly_gross, 2),
        "total_deductions": total_deductions,
        "net_pay": net_pay,
        "deduction_breakdown": {k: round(monthly_gross * v, 2) for k, v in tax_config.items()},
        "status": "processed",
        "processed_at": datetime.utcnow().isoformat(),
    }
    _PAYROLL_RUNS.append(payrun)
    return payrun


def check_labor_law_compliance(employee_id: str) -> dict[str, Any]:
    employee = _EMPLOYEES.get(employee_id)
    if not employee:
        return {"error": f"Employee {employee_id} not found"}
    issues = []
    if employee["country"] == "BR" and employee["salary"] < 90000:
        issues.append({"rule": "BR-CLT-MinWage", "severity": "HIGH", "detail": "Salary may fall below Brazil CLT minimums for role level"})
    if employee["country"] == "DE" and employee["tenure_years"] > 2:
        issues.append({"rule": "DE-KSchG-ProtectedEmployee", "severity": "INFO", "detail": "Employee has full termination protection under German law"})
    return {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "country": employee["country"],
        "compliant": len([i for i in issues if i["severity"] == "HIGH"]) == 0,
        "issues": issues,
        "checked_at": datetime.utcnow().isoformat(),
    }
