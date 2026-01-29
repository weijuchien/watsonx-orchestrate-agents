from ibm_watsonx_orchestrate.agent_builder.tools import tool


def _norm_str(v, default: str) -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _needs_manual_review(context: dict, classification_tag: str) -> bool:
    """Heuristic manual-review trigger.

    In your pipeline, the authoritative decision should come from evaluate_risk.
    This heuristic is only used when generate_data_plan is called standalone.
    """
    data = context.get("data", {}) or {}
    ext = context.get("external_collaborators", {}) or {}
    sensitivity = (data.get("sensitivity", {}) or {}).get("level", "")
    sensitivity = str(sensitivity).strip().lower()
    has_external = bool(ext.get("has_external_collaborators"))

    if classification_tag.strip().lower() == "restricted":
        return True
    if sensitivity in {"high", "restricted", "sensitive"}:
        return True
    if has_external:
        return True
    return False


@tool
def generate_data_plan(
    context: dict,
    classification_tag: str,
    manual_review_required: bool = None,
    manual_review_reason: str = "",
) -> dict:
    """
    Generate a personalized data management plan summary.

    Args:
        context (dict): Composite JSON object with keys:
            - data
            - external_collaborators
            - project
            - researcher
        classification_tag (str): Tag such as "confidential", "restricted", etc.
        manual_review_required (bool, optional): If provided, overrides heuristic.
        manual_review_reason (str, optional): Optional free-text reason for manual review.

    Returns:
        dict: Includes:
          - classification_tag, storage_location, retention_policy, notes
          - manual_review_required, manual_review_reason
          - user_message (READY-TO-PRINT, verbatim)
    """

    # Extract nested fields safely
    data = context.get("data", {}) or {}
    project = context.get("project", {}) or {}
    researcher = context.get("researcher", {}) or {}

    project_title = _norm_str(project.get("title"), "Unknown Project")
    researcher_name = _norm_str(researcher.get("researcher_name"), "Researcher")
    location = _norm_str((data.get("storage", {}) or {}).get("location"), "Unknown")
    sensitivity = _norm_str((data.get("sensitivity", {}) or {}).get("level"), "unknown")

    tag = _norm_str(classification_tag, "public").lower()

    # If the pipeline already decided manual review, respect it.
    if manual_review_required is None:
        manual_review_required = _needs_manual_review(context, tag)
    manual_review_reason = _norm_str(manual_review_reason, "")

    plan = {
        "classification_tag": tag,
        "storage_location": location,
        "project_title": project_title,
        "researcher_name": researcher_name,
        "retention_policy": "",
        "notes": "",
        "manual_review_required": bool(manual_review_required),
        "manual_review_reason": manual_review_reason,
    }

    # Assign retention policy + notes based on classification
    if tag == "restricted":
        plan["retention_policy"] = (
            "Store on secure, access-controlled systems only. "
            "Retain for a minimum of 10 years or per project-specific regulatory requirements. "
            "Data must be encrypted at rest and in transit. Limit access to approved personnel only."
        )
        plan["notes"] = (
            f"Hello {researcher_name}, your project '{project_title}' data is restricted ({sensitivity}). "
            f"Current storage location: {location}."
        )

    elif tag == "confidential":
        plan["retention_policy"] = (
            "Store in approved institutional storage. Retain for at least 5 years or per relevant policies. "
            "Access should be limited to project team members."
        )
        plan["notes"] = (
            f"Hello {researcher_name}, your project '{project_title}' data is confidential ({sensitivity}). "
            f"Current storage location: {location}."
        )

    else:  # public
        plan["retention_policy"] = (
            "Store in general-purpose institutional repositories. Retain for at least 3 years. "
            "Data can be shared openly with proper attribution."
        )
        plan["notes"] = (
            f"Hello {researcher_name}, your project '{project_title}' data is public ({sensitivity}). "
            f"Current storage location: {location}."
        )

    # Build the exact user-facing message you want (agent should print verbatim)
    header = f"Hello {researcher_name}, your project \"{project_title}\" data management plan is ready:"

    user_lines = [
        header,
        "",
        f"Classification: {plan['classification_tag']}",
        f"Storage location: {plan['storage_location']}",
        f"Retention guidance: {plan['retention_policy']}",
        f"Notes: {plan['notes']}",
    ]

    if plan["manual_review_required"]:
        reason = plan["manual_review_reason"].strip()
        if not reason:
            reason = "This project requires manual review due to higher-sensitivity data and/or external collaborators."

        user_lines.extend(
            [
                "",
                f"The project \"{project_title}\" requires manual review.",
                "",
                "Manual-review notice:",
                "",
                reason,
                "",
                "A compliance specialist will review the storage plan, and a designated reviewer will assess the overall data-handling approach. I’ll keep you posted on the next steps.",  # noqa: E501
            ]
        )

    plan["user_message"] = "\n".join(user_lines)

    plan["message"] = plan["user_message"]

    return plan
