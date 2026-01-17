from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class Cinema:
    id: int
    name: str
    address: str


@dataclass
class Seat:
    row: str
    number: int
    is_available: bool = True


@dataclass
class Hall:
    id: int
    name: str
    cinema_id: int
    rows: int = 8
    seats_per_row: int = 10
    seats: List[Seat] = field(default_factory=list)


@dataclass
class Session:
    id: int
    movie_title: str
    cinema_id: int
    hall_id: int
    start_time: str
    session_date: str
    price: float = 250.0
    seats: List[Seat] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())