from pydantic import BaseModel


class NotificationRequest(BaseModel):
    ticket_id: int
    message: str
    email: str = None
    event_type: str = "purchase"  # purchase, cancellation, refund