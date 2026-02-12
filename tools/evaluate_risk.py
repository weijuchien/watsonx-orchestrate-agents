from ibm_watsonx_orchestrate.agent_builder.tools import tool


def _resolve_intake_context(context) -> dict:
    """
    Normalize any wrapped payload to the canonical intake object with
    top-level keys: data, project, researcher, external_collaborators.

    Handles all known wrapping scenarios from the watsonx Orchestrate framework:
      1. JSON string → parse first
      2. Already correct (has "data" + "project" at top) → use as-is
      3. Wrapped in "intake" key (from flatten_params) → unwrap
      4. Wrapped in "context" key (framework passes entire args object) → unwrap
      5. Otherwise → return as-is
    """
    import json as _json

    # Handle string input (JSON serialized)
    if isinstance(context, str):
        try:
            context = _json.loads(context)
        except (ValueError, TypeError):
            return {}

    if not isinstance(context, dict):
        return {}

    # Already has expected top-level keys — use directly
    if "data" in context and "project" in context:
        return context

    # Wrapped in "intake" key (from flatten_params output)
    if isinstance(context.get("intake"), dict):
        return context["intake"]

    # Wrapped in "context" key (framework may pass entire args object as context param)
    if isinstance(context.get("context"), dict):
        return context["context"]

    return context


@tool
def evaluate_risk(context: dict) -> dict:
    """
    Evaluate governance risk and classification based on composite JSON input.

    Args:
        context (dict): Composite JSON object with keys:
            - data
            - external_collaborators
            - project
            - researcher

        Nested fields:
            - data.storage.approved_storage
            - data.sensitivity.level
            - data.data_types (optional)
            - data.human_participants.involves_humans (optional)
            - external_collaborators.has_external_collaborators

    Returns:
        dict: {
            "requires_approval": bool,
            "requires_review": bool,
            "classification_tag": str
        }
    """

    context = _resolve_intake_context(context)

    # Extract nested objects
    data = context.get("data", {})
    storage = data.get("storage", {})
    sensitivity = data.get("sensitivity", {}).get("level", "").lower()
    data_types = [dt.lower() for dt in data.get("data_types", [])]
    human_participants = data.get("human_participants", {}).get("involves_humans", False)

    external = context.get("external_collaborators", {}).get("has_external_collaborators", False)

    result = {
        "requires_approval": False,
        "requires_review": False,
        "classification_tag": "public"
    }

    # Storage approval check
    if storage.get("approved_storage") is False:
        result["requires_approval"] = True

    # High sensitivity requires manual review
    if sensitivity == "high":
        result["requires_review"] = True
        result["classification_tag"] = "restricted"
        return result  # early return since high sensitivity is top priority

    # Classification rules for medium/low
    if sensitivity == "medium":
        result["classification_tag"] = "confidential"
    elif sensitivity == "low":
        result["classification_tag"] = "public"

    # Further refine if human participants involved
    if human_participants and sensitivity != "low":
        result["classification_tag"] = "restricted"
        result["requires_review"] = True

    # Special data types override
    if any(dt in ["genomic", "special"] for dt in data_types):
        result["classification_tag"] = "restricted"
        result["requires_review"] = True

    return result
