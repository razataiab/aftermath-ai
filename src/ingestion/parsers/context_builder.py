from typing import List, Dict

def build_conversation_context(messages: List[Dict]) -> str:
    lines = []
    for msg in messages:
        ts = msg.get("timestamp", "")
        user = msg.get("user_id", "unknown")
        text = msg.get("text", "")
        lines.append(f"[{user}]: {text}")
    return "\n".join(lines)
