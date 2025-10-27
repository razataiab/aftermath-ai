from typing import Dict

def parse_interaction_payload(payload: Dict) -> Dict:
    out = {}
    out["channel_id"] = payload.get("channel_id") or payload.get("channel", {}).get("id")
    user = payload.get("member", {}).get("user") or payload.get("user") or {}
    out["user_id"] = user.get("id") or payload.get("author", {}).get("id")
    out["channel_name"] = payload.get("channel", {}).get("name") or ""
    out["trigger_platform"] = payload.get("trigger_platform", "discord_interaction")
    return out
