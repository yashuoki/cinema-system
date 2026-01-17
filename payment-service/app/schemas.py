from pydantic import BaseModel


class PaymentInitRequest(BaseModel):
    ticket_id: int
    amount: float
    email: str = None


class PaymentResultResponse(BaseModel):
    ticket_id: int
    status: str
    message: str = ""


class RefundRequest(BaseModel):
    ticket_id: int
    reason: str = "User requested refund"


class RefundResponse(BaseModel):
    ticket_id: int
    status: str
    refunded_amount: float
    message: str = ""