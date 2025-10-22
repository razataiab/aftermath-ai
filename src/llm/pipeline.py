from typing import List, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

from src.app.core.config import settings
from src.app.core.models import Incident

OPENAI_API_KEY = settings.OPENAI_API_KEY

class ModelClient:
    def __init__(self, provider: str = "openai", model_name: str = "gpt-5-postmortem"):
        self.provider = provider
        self.model_name = model_name
        self.client = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )

    @classmethod
    def select(cls, provider: str = "openai", model_name: str = "gpt-4o") -> "ModelClient":
        return cls(provider, model_name)

    def generate(self, messages: List[dict]) -> str:
        lc_msgs = []
        for m in messages:
            if m["role"] == "system":
                lc_msgs.append(SystemMessage(content=m["content"]))
            elif m["role"] == "user":
                lc_msgs.append(HumanMessage(content=m["content"]))
        response = self.client(lc_msgs)
        return response.content


POSTMORTEM_TEMPLATE = """
You are a senior SRE generating an incident postmortem.

Context:
{{context}}

Instructions:
- Deliver a structured postmortem with clear root cause
- Timeline must be explicit (chronological)
- No filler language
- Cite message sources inline using user_id
- Everything MUST come from the provided incident context

Output format:
1. Summary
2. Impact
3. Timeline
4. Root Cause
5. Remediations
6. Follow-ups
""".strip()


class AgentState(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setdefault("incident", None)
        self.setdefault("postmortem", None)
        self.setdefault("valid", False)


def build_slack_context(incident: Incident) -> str:
    """Format the Slack conversation as `user_id: message` per line."""
    lines = []
    for msg in incident.conversation:
        lines.append(f"{msg.user_id}: {msg.text}")
    return "\n".join(lines)


def slack_tool_func(state: AgentState) -> str:
    """Actual implementation of Slack tool that reads from Incident."""
    incident: Incident = state["incident"]
    return build_slack_context(incident)


slack_tool = Tool(
    name="SlackContext",
    func=lambda incident_id_or_state: slack_tool_func(incident_id_or_state),
    description="Returns previously ingested Slack messages for this incident.",
)

TOOLS = [slack_tool]


def synthesize_postmortem(state: AgentState, model: ModelClient):
    llm_agent = initialize_agent(
        tools=TOOLS,
        llm=model.client,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False
    )

    incident: Incident = state["incident"]
    context = build_slack_context(incident)

    prompt = POSTMORTEM_TEMPLATE.replace("{{context}}", context)

    state["postmortem"] = llm_agent.run(prompt)
    return state


def validate_postmortem(state: AgentState, model: ModelClient):
    check_query = f"Is the following postmortem complete and properly formatted? Respond YES or NO.\n\n{state['postmortem']}"
    res = model.generate([
        {"role": "system", "content": "You are a validator."},
        {"role": "user", "content": check_query},
    ])
    state["valid"] = "YES" in res.upper()
    return state


class PostmortemAgent:
    def __init__(self, model_client: Optional[ModelClient] = None):
        self.model = model_client or ModelClient.select()

    def run(self, incident: Incident) -> str:
        state = AgentState(incident=incident)

        state = synthesize_postmortem(state, self.model)
        state = validate_postmortem(state, self.model)

        return state.get("postmortem", "No output generated.")


__all__ = [
    "ModelClient",
    "PostmortemAgent",
    "POSTMORTEM_TEMPLATE",
    "AgentState",
]