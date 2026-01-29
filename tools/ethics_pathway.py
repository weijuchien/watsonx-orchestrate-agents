import json
from typing import Any, List, Dict, Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool


def _normalize_participant_types(values: Optional[List[Any]]) -> List[str]:
    if not values:
        return []
    out = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            out.append(s)
    return out


def _assess_risk(
    involves_humans: bool,
    participant_type: List[str],
    data_sensitivity_level: str = "",
) -> Dict[str, str]:
    """
    Very simple heuristic risk assessment (starter version).
    You can replace this with richer rules later.
    """
    level = "(not provided)"
    reason = "(not provided)"

    sens = (data_sensitivity_level or "").strip().lower()

    if not involves_humans:
        level = "Low"
        reason = "No human participants involved."
        return {"risk_level": level, "risk_reason": reason}

    # If humans involved, default at least Medium
    level = "Medium"
    reason = "Human participants involved."

    # Escalate to High for more sensitive contexts (simple examples)
    high_signals = {"high", "sensitive", "restricted", "health", "medical", "biometric"}
    if any(x in sens for x in high_signals):
        level = "High"
        reason = f"Human participants involved and data sensitivity indicates elevated risk ({data_sensitivity_level})."
        return {"risk_level": level, "risk_reason": reason}

    # Heuristic: certain participant categories may imply higher risk
    pt_lower = {p.lower() for p in participant_type}
    if {"patients", "children", "minors", "vulnerable"} & pt_lower:
        level = "High"
        reason = "Human participants include potentially vulnerable groups (e.g., patients/minors)."

    return {"risk_level": level, "risk_reason": reason}


def _build_checklist(involves_humans: bool, participant_type: List[str]) -> List[str]:
    """
    Starter checklist generator.
    """
    items: List[str] = []

    if not involves_humans:
        items.append("Confirm no human participant data is collected or processed.")
        items.append("Document rationale for non-human-participant classification.")
        return items

    items.append("Prepare participant information statement and consent process (if applicable).")
    items.append("Describe data collection, storage location, and retention period.")
    items.append("Describe how participants can withdraw and how data will be handled.")
    items.append("Confirm privacy measures (de-identification/anonymisation where possible).")

    pt_lower = {p.lower() for p in participant_type}
    if {"patients", "children", "minors", "vulnerable"} & pt_lower:
        items.append("Include safeguards for vulnerable participants and additional consent requirements.")
        items.append("Consider HREC review due to vulnerable participant group involvement.")

    if not participant_type:
        items.append("Specify participant categories (e.g., students/staff/public/patients).")

    return items


def _build_formatted_report(
    ethics_routing: Dict[str, Any],
    risk_assessment: Dict[str, str],
    checklist: List[str],
    create_ticket: bool,
    ticket: Optional[Dict[str, Any]],
    note: str,
) -> str:
    """Build a human-readable markdown report for chat display."""
    lines: List[str] = []

    # Section 1: Ethics Routing (table)
    lines.append("## Ethics Routing")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    for k, v in ethics_routing.items():
        lines.append(f"| {k} | {_fmt_cell(v)} |")
    lines.append("")

    # Section 2: Risk Assessment (table)
    lines.append("## Risk Assessment")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    for k, v in risk_assessment.items():
        lines.append(f"| {k} | {_fmt_cell(v)} |")
    lines.append("")

    # Section 3: Checklist (numbered list)
    lines.append("## Checklist")
    for i, item in enumerate(checklist, 1):
        lines.append(f"{i}. {item}")
    lines.append("")

    # Section 4: Ticket status
    lines.append("## Ticket Status")
    lines.append(f"- **Ticket created:** {'Yes' if create_ticket else 'No'}")
    if ticket:
        lines.append("- **Assigned to:** " + str(ticket.get("assigned_group", "—")))
        lines.append("- **Title:** " + str(ticket.get("title", "—")))
        fields = ticket.get("fields") or {}
        if fields:
            lines.append("")
            lines.append("### Ticket fields")
            for k, v in fields.items():
                lines.append(f"- **{k}:** {_fmt_cell(v)}")
    lines.append("")

    # Note
    lines.append("---")
    lines.append(f"**Note:** {note}")
    return "\n".join(lines)


def _fmt_cell(v: Any) -> str:
    """Format a value for a table cell or inline display (one line, safe for markdown)."""
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (list, dict)):
        s = json.dumps(v, ensure_ascii=False)
        return s[:80] + "…" if len(s) > 80 else s
    s = str(v).replace("\n", " ").strip()
    return s[:80] + "…" if len(s) > 80 else s


@tool(
    name="ethics_pathway",
    description="Derive ethics routing + risk assessment and optionally create an intake ticket payload (rule-based).",
)
def ethics_pathway(
    researcher_name: str,
    researcher_email: str,
    faculty: str,
    project_title: str,
    project_summary: str,
    involves_humans: bool,
    participant_type: Optional[List[Any]] = None,
    data_sensitivity_level: str = "",
) -> Dict[str, Any]:
    """
    Args:
        researcher_name: Researcher full name.
        researcher_email: Researcher email.
        faculty: Faculty/department.
        project_title: Project title.
        project_summary: Project summary.
        involves_humans: True if the project involves human participants/data.
        participant_type: Participant categories (e.g., ["students","staff"]).
        data_sensitivity_level: Optional sensitivity hint (e.g., "Low/Medium/High", "Health", etc.)
    Returns:
        ethics_routing, risk_assessment, checklist, create_ticket, ticket, note
    """
    participant_type_norm = _normalize_participant_types(participant_type)

    # 1) Determine if we create a ticket
    create_ticket = bool(involves_humans)

    # 2) Compute risk + checklist internally (outputs)
    risk_assessment = _assess_risk(create_ticket, participant_type_norm, data_sensitivity_level)
    checklist = _build_checklist(create_ticket, participant_type_norm)

    # 3) Routing reason internally (output)
    routing_reason = (
        "Human participants involved -> ticket created and assigned to Ticket Analyst for triage."
        if create_ticket else
        "No human participants -> no ticket created, guidance only."
    )

    ethics_routing = {
        "ticket_required": create_ticket,
        "initial_owner": "Ticket Analyst" if create_ticket else None,
        "routing_reason": routing_reason,
    }

    # 4) Optional ticket payload
    ticket = None
    if create_ticket:
        recommended_escalation = (
            "Human Research Ethics Committee (HREC)"
            if risk_assessment.get("risk_level") == "High"
            else "Research Office (Low-risk)"
        )
        ticket = {
            "title": f"Ethics Intake: {project_title}",
            "assigned_group": "Ticket Analyst",
            "fields": {
                "researcher_name": researcher_name,
                "researcher_email": researcher_email,
                "faculty": faculty,
                "project_title": project_title,
                "project_summary": project_summary,
                "human_participants": True,
                "participant_type": participant_type_norm,
                "data_sensitivity_level": data_sensitivity_level,
                "recommended_escalation": recommended_escalation,
                "ethics_routing": ethics_routing,
                "risk_assessment": risk_assessment,
                "checklist": checklist,
            },
        }

    note = "Guidance only. No ethics approval is granted by this agent."
    formatted_report = _build_formatted_report(
        ethics_routing, risk_assessment, checklist, create_ticket, ticket, note
    )

    return {
        "ethics_routing": ethics_routing,
        "risk_assessment": risk_assessment,
        "checklist": checklist,
        "create_ticket": create_ticket,
        "ticket": ticket,
        "note": note,
        "formatted_report": formatted_report,
    }
