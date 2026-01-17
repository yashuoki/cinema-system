import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.logger import logger
from app.schemas import ReserveTicketRequest, TicketResponse, GetTicketsBySessionRequest
from app.models import Ticket, TicketStatus
from app.storage import tickets
from app.session_client import check_seat_available, mark_seat_as_reserved, mark_seat_as_available
from app.logging_service import log_action
from typing import List

app = FastAPI(
    title="Ticket Service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Файловое хранилище
DATA_DIR = "/app/data"
TICKETS_FILE = f"{DATA_DIR}/tickets.json"

def ensure_data_dir():
    """Создать директорию для данных если не существует"""
    os.makedirs(DATA_DIR, exist_ok=True)

def save_tickets():
    """Сохранить билеты в файл"""
    ensure_data_dir()
    tickets_data = {}
    for ticket_id, ticket in tickets.items():
        tickets_data[ticket_id] = {
            "id": ticket.id,
            "session_id": ticket.session_id,
            "row": ticket.row,
            "number": ticket.number,
            "status": ticket.status.value,
            "price": ticket.price,
            "email": ticket.email
        }
    
    with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tickets_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Tickets saved to {TICKETS_FILE}")

def load_tickets():
    """Загрузить билеты из файла"""
    if not os.path.exists(TICKETS_FILE):
        logger.info("Tickets file not found, using default data")
        return
    
    try:
        with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
            tickets_data = json.load(f)
        
        tickets.clear()
        for ticket_id, ticket_data in tickets_data.items():
            ticket = Ticket(
                id=ticket_data["id"],
                session_id=ticket_data["session_id"],
                row=ticket_data["row"],
                number=ticket_data["number"],
                status=TicketStatus(ticket_data["status"]),
                price=ticket_data["price"],
                email=ticket_data.get("email", "")
            )
            tickets[int(ticket_id)] = ticket
        
        logger.info(f"Loaded {len(tickets)} tickets from file")
    except Exception as e:
        logger.error(f"Error loading tickets: {e}")

# Загружаем данные при старте
load_tickets()

ticket_id_seq = 1


@app.on_event("startup")
def startup():
    logger.info("Ticket Service started")


@app.get("/tickets", response_model=List[TicketResponse])
def get_all_tickets():
    """Получить все билеты"""
    logger.info("GET /tickets")
    return list(tickets.values())


@app.get("/tickets/session/{session_id}", response_model=List[TicketResponse])
def get_tickets_by_session(session_id: int):
    """Получить все билеты для конкретного сеанса"""
    logger.info(f"GET /tickets/session/{session_id}")
    result = [t for t in tickets.values() if t.session_id == session_id]
    return result


@app.post("/api/ticket/tickets/reserve", response_model=TicketResponse)
def reserve_ticket_api(request: ReserveTicketRequest):
    """Забронировать билет"""
    logger.info(f"POST /api/ticket/tickets/reserve - session {request.session_id}, seat {request.row}{request.number}")
    
    # Проверяем доступность места
    if not check_seat_available(request.session_id, request.row, request.number):
        raise HTTPException(status_code=400, detail="Seat not available")
    
    # Создаем билет
    global ticket_id_seq
    ticket = Ticket(
        id=ticket_id_seq,
        session_id=request.session_id,
        row=request.row,
        number=request.number,
        status=TicketStatus.RESERVED,
        price=request.price,
        email=request.email
    )
    tickets[ticket_id_seq] = ticket
    ticket_id_seq += 1
    
    # Помечаем место как занято
    mark_seat_as_reserved(request.session_id, request.row, request.number)
    
    # Сохраняем в файл
    save_tickets()
    
    logger.info(f"Ticket {ticket.id} reserved successfully")
    
    # Логируем действие пользователя
    log_action(
        action="RESERVE_TICKET",
        user_id=request.email or "anonymous",
        details={
            "ticket_id": ticket.id,
            "session_id": ticket.session_id,
            "row": ticket.row,
            "number": ticket.number,
            "price": ticket.price,
            "email": ticket.email
        }
    )
    
    return ticket


@app.post("/tickets/reserve", response_model=TicketResponse)
def reserve_ticket(request: ReserveTicketRequest):
    """Забронировать билет"""
    global ticket_id_seq

    logger.info(f"Reserve ticket request: {request}")

    # Проверить доступность места
    if not check_seat_available(request.session_id, request.row, request.number):
        logger.warning(f"Seat {request.row}{request.number} not available")
        raise HTTPException(status_code=400, detail="Seat not available")

    # Создать билет
    ticket = Ticket(
        id=ticket_id_seq,
        session_id=request.session_id,
        row=request.row,
        number=request.number,
        price=request.price,
        status=TicketStatus.RESERVED,
        email=request.email
    )
    tickets[ticket_id_seq] = ticket
    ticket_id_seq += 1

    # Пометить место как занятое
    mark_seat_as_reserved(request.session_id, request.row, request.number)

    logger.info(f"Ticket reserved: {ticket}")
    return ticket


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int):
    """Получить информацию о билете"""
    logger.info(f"GET /tickets/{ticket_id}")
    
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return ticket


@app.post("/tickets/confirm/{ticket_id}", response_model=TicketResponse)
def confirm_ticket(ticket_id: int):
    """Подтвердить билет (оплачен)"""
    logger.info(f"POST /tickets/confirm/{ticket_id}")
    
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = TicketStatus.SOLD
    
    # Сохраняем изменения
    save_tickets()
    
    logger.info(f"Ticket sold: {ticket}")
    
    # Логируем действие пользователя
    log_action(
        action="CONFIRM_TICKET",
        user_id=ticket.email or "anonymous",
        details={
            "ticket_id": ticket.id,
            "session_id": ticket.session_id,
            "row": ticket.row,
            "number": ticket.number,
            "price": ticket.price,
            "email": ticket.email
        }
    )
    
    return ticket


@app.post("/tickets/cancel/{ticket_id}", response_model=TicketResponse)
def cancel_ticket(ticket_id: int):
    """Отменить билет"""
    logger.info(f"POST /tickets/cancel/{ticket_id}")
    
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = TicketStatus.CANCELLED
    
    # Освобождаем место
    mark_seat_as_available(ticket.session_id, ticket.row, ticket.number)
    
    # Сохраняем изменения
    save_tickets()
    
    logger.info(f"Ticket cancelled: {ticket}")
    
    # Логируем действие пользователя
    log_action(
        action="CANCEL_TICKET",
        user_id=ticket.email or "anonymous",
        details={
            "ticket_id": ticket.id,
            "session_id": ticket.session_id,
            "row": ticket.row,
            "number": ticket.number,
            "price": ticket.price,
            "email": ticket.email
        }
    )
    
    return ticket