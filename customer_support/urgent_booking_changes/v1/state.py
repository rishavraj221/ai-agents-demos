from typing import TypedDict, Optional

class AgentState(TypedDict):
    user_input: str
    booking_id: Optional[str]
    api_key: Optional[str]
    intent: Optional[str]
    booking_details: Optional[dict]
    confirmation: Optional[bool]
    error: Optional[str]