from pydantic import BaseModel
from typing import List, Optional


class CinemaSchema(BaseModel):
    id: int
    name: str
    address: str


class SeatSchema(BaseModel):
    row: str
    number: int
    is_available: bool


class UpdateSeatSchema(BaseModel):
    is_available: bool


class HallSchema(BaseModel):
    id: int
    name: str
    cinema_id: int
    rows: int
    seats_per_row: int


class SessionSchema(BaseModel):
    id: int
    movie_title: str
    cinema_id: int
    hall_id: int
    start_time: str
    session_date: str
    price: float


class CreateSessionSchema(BaseModel):
    movie_title: str
    cinema_id: int
    hall_id: int
    start_time: str
    session_date: str
    price: float


class CreateMultipleSessionsSchema(BaseModel):
    movie_title: str
    cinema_id: int
    hall_id: int
    start_times: List[str]  # Список времен сеансов
    price: float


class UpdateSessionSchema(BaseModel):
    price: Optional[float] = None
    movie_title: Optional[str] = None