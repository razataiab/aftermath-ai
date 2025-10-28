from typing import List, Optional
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

from src.app.core.config import settings
from src.app.core.models import Incident

OPENAI_API_KEY = settings.OPENAI_API_KEY
LOG_LENGTH_LIMIT = 10000 

class ModelClient:
    def __init__(self, provider: str = "openai", model_name: str = None):
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
- Cite message sources inline using user_id and source (e.g. user123@slack)
- Everything MUST come from the provided incident context (conversation and deployment logs)

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

def build_multi_source_context(incident: Incident) -> str:
    """
    Format messages with source tags:
      [slack] U123: message
      [discord] 98765: message
      [teams] S-1: message
    """
    lines = []
    for msg in incident.conversation:
        source = msg.source or incident.source or "unknown"
        lines.append(f"[{source}] {msg.user_id}: {msg.text}")
    return "\n".join(lines)

def slack_tool_func(state: AgentState) -> str:
    """Return formatted context (keeps compatibility with existing tools)"""
    incident: Incident = state["incident"]
    return build_multi_source_context(incident)

slack_tool = Tool(
    name="ConversationContext",
    func=lambda incident_state: slack_tool_func(incident_state),
    description="Returns previously ingested messages for this incident from any source (Slack/Discord/Teams).",
)

TOOLS = [slack_tool]

def summarize_logs(logs: str, model_client: ModelClient) -> str:
    print(f"Summarizing {len(logs)} chars of log data...")
    SUMMARIZE_PROMPT = """
    You are a log summarization bot. Summarize the following deployment logs.
    Focus *only* on errors, warnings, failures, and key success markers (e.g., "deployment successful", "service started").
    Be very concise and use bullet points for key findings.
    """.strip()
    
    try:
        summary = model_client.generate([
            {"role": "system", "content": SUMMARIZE_PROMPT},
            {"role": "user", "content": logs},
        ])
        return f"--- LOG SUMMARY ---\n{summary}\n--- END OF SUMMARY ---"
    except Exception as e:
        print(f"Failed to summarize logs: {e}. Truncating instead.")
        return logs[:LOG_LENGTH_LIMIT] # Fallback to truncation

def synthesize_postmortem(state: AgentState, model: ModelClient):
    llm_agent = initialize_agent(
        tools=TOOLS,
        llm=model.client,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False
    )

    incident: Incident = state["incident"]
    
    conversation_context = build_multi_source_context(incident)
    full_context = [conversation_context]
    
    deployment_logs = incident.deployment_logs
    
    if deployment_logs:
        if len(deployment_logs) > LOG_LENGTH_LIMIT:
            print(f"Deployment logs exceed {LOG_LENGTH_LIMIT} chars, summarizing...")
            deployment_logs = summarize_logs(deployment_logs, model)
        
        full_context.append(f"\n\n--- DEPLOYMENT LOGS ---\n{deployment_logs}")

    context = "\n".join(full_context)
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