from dataclasses import dataclass
from enum import Enum


class TicketStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    CANCELLED = "CANCELLED"


@dataclass
class Ticket:
    id: int
    session_id: int
    row: str
    number: int
    status: TicketStatus
    price: float = 250.0
    email: str = ""