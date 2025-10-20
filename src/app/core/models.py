from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

class Message(BaseModel):
    user_id: str
    username: str
    text: str
    timestamp: datetime

class Conversation(BaseModel):
    channel_id: str
    channel_name: str
    messages: List[Message]

class PostmortemRun(BaseModel):
    incident_id: str
    channel_id: str
    run_id: str
    run_timestamp: datetime
    invoked_by: str
