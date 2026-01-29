from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool
def evaluate_storage_location(context: dict) -> dict:
    """
    Checks whether the current storage location is approved based on sensitivity and external collaborators.

    Args:
        context (dict): Composite JSON object with keys:
            - data
            - external_collaborators

    Returns:
        dict: {
            "is_approved": bool,
            "location_matrix": list[str]
        }
    """

    data = context.get("data", {})
    external_collaborators = context.get("external_collaborators", {})

    # Storage policy matrix
    storage_policy_matrix = {
        "low": {
            "no": {
                "approved_locations": [
                    "Institutional OneDrive",
                    "University SharePoint Site"
                ]
            },
            "yes": {
                "approved_locations": [
                    "Microsoft Teams",
                    "Institutional Dropbox"
                ]
            }
        },
        "medium": {
            "no": {
                "approved_locations": [
                    "University Research-NAS",
                    "Institutional OneDrive"
                ]
            },
            "yes": {
                "approved_locations": [
                    "Microsoft SharePoint",
                    "LabArchives"
                ]
            }
        },
        "high": {
            "no": {
                "approved_locations": [
                    "Secure eResearch Platform (SeRP)",
                    "On-Premise High-Security Server"
                ]
            },
            "yes": {
                "approved_locations": [
                    "Multi-Institutional Secure Cloud Tenant",
                    "Nectar Research Cloud"
                ]
            }
        }
    }

    # Extract fields
    sensitivity = str(data.get("sensitivity", {}).get("level", "")).lower()
    has_external = external_collaborators.get("has_external_collaborators", False)
    external_key = "yes" if has_external else "no"
    current_location = str(data.get("storage", {}).get("location", "")).strip()

    # Default outputs
    is_approved = False
    location_matrix = []
    approved_locations = []

    # Lookup policy
    policy = storage_policy_matrix.get(sensitivity, {}).get(external_key)
    if policy:
        approved_locations = policy.get("approved_locations", [])
        location_matrix = approved_locations
        is_approved = current_location.lower() in [loc.lower() for loc in approved_locations]

    message = (
        f"The current storage location {current_location} is approved for the project."
        if is_approved else
        f"The current storage location {current_location} is not approved for the project. "
        f"Please move the data to one of the approved locations (e.g., {approved_locations[0] if approved_locations else 'an approved location'}) before proceeding. "  # noqa: E501
        f"If you need assistance selecting an appropriate approved location, let me know!"
    )

    return {
        "is_approved": is_approved,
        "current_location": current_location,
        "location_matrix": location_matrix,
        "message": message
    }
