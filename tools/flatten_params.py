from typing import Any, Dict, List
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool(
    name="flatten_params",
    description="Map nested intake payload to ethics_pathway flat arguments. "
    "Returns 'flat' (for ethics) and 'intake' (for data_management_agent in flow)."
)
def flatten_params(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map nested intake JSON to flat params for ethics_pathway.
    Also returns the original intake so the flow can pass it to data_management_agent.

    Args:
        payload: Nested intake with meta/project/researcher/approver/ai/data/external_collaborators.

    Returns:
        Dict with "flat" (researcher_name, faculty, etc.) and "intake" (original payload).
    """
    researcher = payload.get("researcher", {}) or {}
    project = payload.get("project", {}) or {}
    data = payload.get("data", {}) or {}

    affiliation = (researcher.get("researcher_affiliation", {}) or {})
    human = (data.get("human_participants", {}) or {})
    sensitivity = (data.get("sensitivity", {}) or {})

    participant_type: List[Any] = human.get("data_details") or []
    if not isinstance(participant_type, list):
        participant_type = []

    flat = {
        "researcher_name": (researcher.get("researcher_name") or "").strip(),
        "researcher_email": (researcher.get("researcher_email") or "").strip(),
        "faculty": (affiliation.get("school_faculty") or "").strip(),
        "project_title": (project.get("title") or "").strip(),
        "project_summary": (project.get("summary") or "").strip(),
        "involves_humans": bool(human.get("involves_humans")),
        "participant_type": participant_type,
        "data_sensitivity_level": (sensitivity.get("level") or "").strip(),
    }
    return {"flat": flat, "intake": payload}
