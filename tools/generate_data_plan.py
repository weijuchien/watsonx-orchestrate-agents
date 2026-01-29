from ibm_watsonx_orchestrate.agent_builder.tools import tool

@tool
def generate_data_plan(context: dict, classification_tag: str) -> dict:
    """
    Generate a personalized data management plan summary.

    Args:
        context (dict): Composite JSON object with keys:
            - data
            - external_collaborators
            - project
            - researcher
        classification_tag (str): Tag such as "confidential", "restricted", etc.

    Returns:
        dict: A summary for the user, including updated message and retention policy
    """

    # Extract nested fields safely
    data = context.get("data", {})
    project = context.get("project", {})
    researcher = context.get("researcher", {})

    project_title = project.get("title", "Unknown Project")
    researcher_name = researcher.get("researcher_name", "Researcher")
    location = data.get("storage", {}).get("location", "Unknown")
    sensitivity = data.get("sensitivity", {}).get("level", "unknown")

    plan = {
        "classification_tag": classification_tag,
        "storage_location": location,
        "project_title": project_title,
        "researcher_name": researcher_name,
        "retention_policy": ""
    }

    # Assign retention policy and message based on classification
    if classification_tag == "restricted":
        plan["retention_policy"] = (
            "Store on secure, access-controlled systems only. "
            "Retain for a minimum of 10 years or per project-specific regulatory requirements. "
            "Data must be encrypted at rest and in transit. Limit access to approved personnel only."
        )
        plan["message"] = (
            f"Hello {researcher_name}, your project '{project_title}' data has been classified as "
            f"restricted ({sensitivity}). Current storage location: {location}. "
            f"Manual review may be required. Retention guidance: {plan['retention_policy']}"
        )

    elif classification_tag == "confidential":
        plan["retention_policy"] = (
            "Store in approved institutional storage. Retain for at least 5 years or per relevant policies. "
            "Access should be limited to project team members."
        )
        plan["message"] = (
            f"Hello {researcher_name}, your project '{project_title}' data is confidential ({sensitivity}). "
            f"Current storage location: {location}. Retention guidance: {plan['retention_policy']}"
        )

    else:  # public
        plan["retention_policy"] = (
            "Store in general-purpose institutional repositories. Retain for at least 3 years. "
            "Data can be shared openly with proper attribution."
        )
        plan["message"] = (
            f"Hello {researcher_name}, your project '{project_title}' data is public ({sensitivity}). "
            f"Current storage location: {location}. Retention guidance: {plan['retention_policy']}"
        )

    return plan
