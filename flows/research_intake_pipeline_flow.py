from typing import Any, Dict, List

from pydantic import BaseModel, Field

from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow
from ibm_watsonx_orchestrate.flow_builder.flows.constants import START, END


# ---- 1) Define Flow input schema (matches your intake JSON) ----

class Meta(BaseModel):
    request_id: str
    created_at: str
    updated_at: str


class Project(BaseModel):
    stage: str
    title: str
    domain: str
    purpose: str
    summary: str


class ResearcherAffiliation(BaseModel):
    institution: str
    school_faculty: str


class Researcher(BaseModel):
    researcher_name: str
    researcher_email: str
    researcher_affiliation: ResearcherAffiliation


class ApproverAffiliation(BaseModel):
    approver_institution: str
    approver_school_faculty: str


class Approver(BaseModel):
    approver_name: str
    approver_email: str
    approver_affiliation: ApproverAffiliation


class ExternalModelDetails(BaseModel):
    model: str
    provider: str
    service: str


class AIUsage(BaseModel):
    ai_usage_type: str
    decision_support: str
    external_model_used: bool
    external_model_details: ExternalModelDetails


class AI(BaseModel):
    usage: AIUsage


class HumanParticipants(BaseModel):
    involves_humans: bool
    data_details: List[str] = Field(default_factory=list)


class Sensitivity(BaseModel):
    level: str
    rationale: str


class Storage(BaseModel):
    approved_storage: bool
    location: str


class Data(BaseModel):
    vendor: str
    data_types: List[str] = Field(default_factory=list)
    human_participants: HumanParticipants
    sensitivity: Sensitivity
    storage: Storage


class ExternalCollaborators(BaseModel):
    has_external_collaborators: bool
    collaborators: List[Dict[str, Any]] = Field(default_factory=list)


class IntakePayload(BaseModel):
    meta: Meta
    project: Project
    researcher: Researcher
    approver: Approver
    ai: AI
    data: Data
    external_collaborators: ExternalCollaborators


# ---- 2) Define Flow output schema (verbatim outputs) ----

class FlowOutput(BaseModel):
    ethics_output: Dict[str, Any] = Field(description="Raw JSON output returned by ethics_pathway")
    data_mgmt_output: Any = Field(description="Raw output returned by data_management_agent")


@flow(
    name="research_intake_pipeline",
    description="Fixed pipeline: flatten intake -> ethics_pathway -> data_management_agent -> return both outputs verbatim",  # noqa: E501
    input_schema=IntakePayload,
    output_schema=FlowOutput,
)
def build_research_intake_pipeline(aflow: Flow) -> Flow:
    # 1. flatten nested payload → flat ethics params
    flatten_node = aflow.tool(
        "flatten_params",
        name="flatten_params_node",
        description="Map nested intake payload to ethics helper arguments"
    )

    # 2. Ethics Helper Agent
    ethics_agent_node = aflow.agent(
        name="ethics_helper_node",
        agent="ethics_helper_agent",
        description="Determine ethics routing, risk level, and checklist",
        message=(
            "Use the provided parameters to determine ethics pathway, risk level, "
            "and required checklist. Call ethics_pathway as needed."
        ),
    )

    # 3. Data Management Agent
    data_mgmt_node = aflow.agent(
        name="data_management_node",
        agent="data_management_agent",
        description="Assess data handling and storage compliance requirements",
        message="Use the provided intake payload to assess data governance requirements.",
    )

    # Lock sequence: START -> flatten -> ethics -> data_mgmt -> END
    aflow.sequence(
        START,
        flatten_node,
        ethics_agent_node,   # ← ethics FIRST
        data_mgmt_node,      # ← data mgmt SECOND
        END,
    )

    return aflow
