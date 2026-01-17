from pydantic import BaseModel, EmailStr
from enum import Enum


class TicketStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    CANCELLED = "CANCELLED"


class ReserveTicketRequest(BaseModel):
    session_id: int
    row: str
    number: int
    price: float = 250.0
    email: str = None


class TicketResponse(BaseModel):
    id: int
    session_id: int
    row: str
    number: int
    status: TicketStatus
    price: float
    email: str = None


class GetTicketsBySessionRequest(BaseModel):
    session_id: int


class CancelTicketRequest(BaseModel):
    reason: str = "User requested cancellation"