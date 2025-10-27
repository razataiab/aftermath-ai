from typing import Dict

def parse_trigger_payload(payload: Dict) -> Dict:
    out = {}
    if payload.get("value") and isinstance(payload.get("value"), list):
        item = payload["value"][0]
        resource = item.get("resource", "")
        parts = resource.split("/")
        if "channels" in parts:
            try:
                channel_idx = parts.index("channels") + 1
                out["channel_id"] = parts[channel_idx]
            except Exception:
                out["channel_id"] = payload.get("channelId")
    out["channel_id"] = out.get("channel_id") or payload.get("channelId") or payload.get("conversationId") or payload.get("resourceData", {}).get("channelId")
    out["user_id"] = payload.get("from", {}).get("user", {}).get("id") or payload.get("user", {}).get("id") or payload.get("from", {}).get("id")
    out["channel_name"] = payload.get("channelName") or payload.get("resourceData", {}).get("channel", {}).get("displayName", "")
    out["trigger_platform"] = payload.get("trigger_platform") or payload.get("type") or "teams_webhook"
    return out
