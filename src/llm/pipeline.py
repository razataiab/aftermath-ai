from typing import List, Optional
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
import asyncio

from src.ingestion.connectors.slack_connector import retrieve_slack_chat_history, retrieve_slack_user_name

class ModelClient:
    def __init__(self, provider: str = "openai", model_name: str = "gpt-5-postmortem"):
        self.provider = provider
        self.model_name = model_name
        self.client = ChatOpenAI(model=model_name, temperature=0.3)

    @classmethod
    def select(cls, provider: str = "openai", model_name: str = "gpt-5-postmortem") -> "ModelClient":
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
- Timeline must be explicit
- No filler phrases
- Cite sources (slack/github/deploy-log) inline

Output format:
1. Summary
2. Impact
3. Timeline
4. Root Cause
5. Remediations
6. Follow-ups
"""

class AgentState(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setdefault("context", {})
        self.setdefault("postmortem", None)

def fetch_slack_context(incident_id: str) -> str:
    return f"Slack discussion snippet for {incident_id}"

slack_tool = Tool(
    name="Slack",
    func=fetch_slack_context,
    description="Fetch relevant Slack messages for an incident"
)

TOOLS = [slack_tool]

def synthesize_postmortem(state: AgentState, model: ModelClient):
    llm_agent = initialize_agent(
        tools=TOOLS,
        llm=model.client,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=False
    )

    prompt = POSTMORTEM_TEMPLATE.replace(
        "{{context}}",
        f"Incident ID: {state.get('incident_id')}\nPlease fetch Slack/GitHub/deploy logs as needed."
    )

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

    def run(self, incident_id: str, initial_context: dict) -> str:
        state = AgentState(incident_id=incident_id, context=initial_context)

        state = synthesize_postmortem(state, self.model)
        state = validate_postmortem(state, self.model)

        return state.get("postmortem", "No output generated.")

__all__ = [
    "ModelClient",
    "PostmortemAgent",
    "POSTMORTEM_TEMPLATE",
    "AgentState",
]