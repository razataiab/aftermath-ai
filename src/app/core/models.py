from pydantic import BaseModel
from typing import List
from datetime import datetime

class Message(BaseModel):
    user_id: str
    username: str
    text: str
    timestamp: datetime

class Incident(BaseModel):         
    incident_id: str
    channel_id: str
    triggered_by_user_id: str
    triggered_by_user_name: str
    channel_name: str
    conversation: List[Message]