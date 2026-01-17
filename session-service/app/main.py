import json
import os
import re
from datetime import datetime
from collections import Counter
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

from app.schemas import SessionSchema, CreateSessionSchema, SeatSchema, UpdateSeatSchema, HallSchema, UpdateSessionSchema, CinemaSchema, CreateMultipleSessionsSchema
from app.storage import sessions, halls, cinemas
from app.logger import logger
from app.models import Seat
from app.logging_service import log_action, get_logs, LOG_FILE

app = FastAPI(
    title="Session Service",
    docs_url="/docs",
    default_response_class=JSONResponse
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для правильной кодировки
@app.middleware("http")
async def add_charset_header(request, call_next):
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("application/json"):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

# Файловое хранилище
DATA_DIR = "/app/data"
SESSIONS_FILE = f"{DATA_DIR}/sessions.json"
HALLS_FILE = f"{DATA_DIR}/halls.json"

def ensure_data_dir():
    """Создать директорию для данных если не существует"""
    os.makedirs(DATA_DIR, exist_ok=True)

def save_sessions():
    """Сохранить сессии в файл"""
    ensure_data_dir()
    sessions_data = {}
    for session_id, session in sessions.items():
        sessions_data[session_id] = {
            "id": session.id,
            "movie_title": session.movie_title,
            "cinema_id": session.cinema_id,
            "hall_id": session.hall_id,
            "start_time": session.start_time,
            "session_date": session.session_date,
            "price": session.price,
            "seats": [
                {"row": seat.row, "number": seat.number, "is_available": seat.is_available}
                for seat in session.seats
            ]
        }
    
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Sessions saved to {SESSIONS_FILE}")

def load_sessions():
    """Загрузить сессии из файла"""
    if not os.path.exists(SESSIONS_FILE):
        logger.info("Sessions file not found, using default data")
        return
    
    try:
        with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
            sessions_data = json.load(f)
        
        sessions.clear()
        for session_id, session_data in sessions_data.items():
            session_seats = [
                Seat(row=seat["row"], number=seat["number"], is_available=seat["is_available"])
                for seat in session_data["seats"]
            ]
            
            from app.models import Session
            # Простая и надежная логика для session_date
            session_date = session_data.get("session_date")
            if not session_date:
                # Fallback: пробуем извлечь из start_time
                start_time_str = session_data.get("start_time", "")
                if "T" in start_time_str:
                    session_date = start_time_str.split("T")[0]
                elif " " in start_time_str:
                    session_date = start_time_str.split(" ")[0]
                else:
                    session_date = datetime.now().strftime("%Y-%m-%d")
            
            session = Session(
                id=session_data["id"],
                movie_title=session_data["movie_title"],
                cinema_id=session_data.get("cinema_id", 1),  # Для обратной совместимости
                hall_id=session_data["hall_id"],
                start_time=session_data["start_time"],
                session_date=session_date,
                price=session_data["price"],
                seats=session_seats
            )
            sessions[int(session_id)] = session
        
        logger.info(f"Loaded {len(sessions)} sessions from file")
    except Exception as e:
        logger.error(f"Error loading sessions: {e}")

def save_halls():
    """Сохранить залы в файл"""
    ensure_data_dir()
    halls_data = {}
    for hall_id, hall in halls.items():
        halls_data[hall_id] = {
            "id": hall.id,
            "name": hall.name,
            "cinema_id": hall.cinema_id,
            "rows": hall.rows,
            "seats_per_row": hall.seats_per_row,
            "seats": [
                {"row": seat.row, "number": seat.number}
                for seat in hall.seats
            ]
        }
    
    with open(HALLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(halls_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Halls saved to {HALLS_FILE}")

def load_halls():
    """Загрузить залы из файла"""
    if not os.path.exists(HALLS_FILE):
        logger.info("Halls file not found, using default data")
        return
    
    try:
        with open(HALLS_FILE, 'r', encoding='utf-8') as f:
            halls_data = json.load(f)
        
        halls.clear()
        for hall_id, hall_data in halls_data.items():
            hall_seats = [
                Seat(row=seat["row"], number=seat["number"])
                for seat in hall_data["seats"]
            ]
            
            from app.models import Hall
            hall = Hall(
                id=hall_data["id"],
                name=hall_data["name"],
                cinema_id=hall_data.get("cinema_id", 1),  # Для обратной совместимости
                rows=hall_data["rows"],
                seats_per_row=hall_data["seats_per_row"],
                seats=hall_seats
            )
            halls[int(hall_id)] = hall
        
        logger.info(f"Loaded {len(halls)} halls from file")
    except Exception as e:
        logger.error(f"Error loading halls: {e}")

# Загружаем данные при старте
load_sessions()
load_halls()


@app.on_event("startup")
def startup():
    logger.info("Session Service started")


# API для кинотеатров
@app.get("/api/session/cinemas", response_model=List[CinemaSchema])
def get_cinemas_api():
    """Получить все кинотеатры"""
    logger.info("GET /api/session/cinemas")
    return list(cinemas.values())

@app.get("/cinemas", response_model=List[CinemaSchema])
def get_cinemas():
    """Получить все кинотеатры"""
    logger.info("GET /cinemas")
    return list(cinemas.values())


@app.get("/api/session/halls", response_model=List[HallSchema])
def get_halls_api():
    """Получить все залы"""
    logger.info("GET /api/session/halls")
    return [
        HallSchema(id=h.id, name=h.name, cinema_id=h.cinema_id, rows=h.rows, seats_per_row=h.seats_per_row)
        for h in halls.values()
    ]

@app.get("/halls", response_model=List[HallSchema])
def get_halls():
    """Получить все залы"""
    logger.info("GET /halls")
    return [
        HallSchema(id=h.id, name=h.name, cinema_id=h.cinema_id, rows=h.rows, seats_per_row=h.seats_per_row)
        for h in halls.values()
    ]

@app.get("/halls/cinema/{cinema_id}", response_model=List[HallSchema])
def get_halls_by_cinema(cinema_id: int):
    """Получить залы конкретного кинотеатра"""
    logger.info(f"GET /halls/cinema/{cinema_id}")
    return [
        HallSchema(id=h.id, name=h.name, cinema_id=h.cinema_id, rows=h.rows, seats_per_row=h.seats_per_row)
        for h in halls.values() if h.cinema_id == cinema_id
    ]


@app.get("/api/session/sessions", response_model=List[SessionSchema])
def get_sessions_api():
    logger.info("GET /api/session/sessions")
    result = []
    for session in sessions.values():
        result.append(SessionSchema(
            id=session.id,
            movie_title=session.movie_title,
            cinema_id=session.cinema_id,
            hall_id=session.hall_id,
            start_time=session.start_time,
            session_date=session.session_date,
            price=session.price
        ))
    return result

@app.get("/sessions", response_model=List[SessionSchema])
def get_sessions():
    logger.info("GET /sessions")
    return list(sessions.values())


@app.get("/sessions/{session_id}", response_model=SessionSchema)
def get_session(session_id: int):
    logger.info(f"GET /sessions/{session_id}")
    
    session = sessions.get(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@app.get("/api/session/sessions/{session_id}/seats", response_model=List[SeatSchema])
def get_seats_api(session_id: int):
    logger.info(f"GET /api/session/sessions/{session_id}/seats")

    session = sessions.get(session_id)
    if not session:
        logger.error("Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    hall = halls.get(session.hall_id)
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")
    
    return hall.seats

@app.get("/sessions/{session_id}/seats", response_model=List[SeatSchema])
def get_seats(session_id: int):
    logger.info(f"GET /sessions/{session_id}/seats")

    session = sessions.get(session_id)
    if not session:
        logger.error("Session not found")
        raise HTTPException(status_code=404, detail="Session not found")

    return session.seats


@app.put("/api/session/sessions/{session_id}/seats/{row}/{number}", response_model=SeatSchema)
def update_seat_api(session_id: int, row: str, number: int, seat_data: UpdateSeatSchema):
    """Обновить статус места"""
    logger.info(f"PUT /api/session/sessions/{session_id}/seats/{row}/{number}")
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Найти место в сессии
    for seat in session.seats:
        if seat.row == row and seat.number == number:
            seat.is_available = seat_data.is_available
            # Сохраняем изменения
            save_sessions()
            return seat
    
    raise HTTPException(status_code=404, detail="Seat not found")

@app.put("/sessions/{session_id}/seats/{row}/{number}")
def update_seat(session_id: int, row: str, number: int, data: UpdateSeatSchema):
    """Обновить доступность места"""
    logger.info(f"PUT /sessions/{session_id}/seats/{row}/{number} - is_available={data.is_available}")
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    hall = halls.get(session.hall_id)
    if not hall:
        raise HTTPException(status_code=404, detail="Hall not found")
    
    for seat in hall.seats:
        if seat.row == row and seat.number == number:
            seat.is_available = data.is_available
            logger.info(f"Seat {row}{number} updated to is_available={data.is_available}")
            return {"status": "ok", "row": row, "number": number, "is_available": data.is_available}
    
    raise HTTPException(status_code=404, detail="Seat not found")


@app.post("/api/session/sessions", response_model=SessionSchema)
def create_session_api(data: CreateSessionSchema):
    """Создать новый сеанс"""
    logger.info(f"POST /api/session/sessions - {data.movie_title} в {data.start_time}")
    
    if data.cinema_id not in cinemas:
        raise HTTPException(status_code=400, detail="Cinema not found")
    
    if data.hall_id not in halls:
        raise HTTPException(status_code=400, detail="Hall not found")
    
    # Проверка что зал принадлежит указанному кинотеатру
    hall = halls.get(data.hall_id)
    if hall.cinema_id != data.cinema_id:
        raise HTTPException(status_code=400, detail="Hall does not belong to this cinema")
    
    # Используем переданную дату, если есть, иначе текущую
    if hasattr(data, 'session_date') and data.session_date:
        session_date = data.session_date
    else:
        # Извлекаем дату из start_time если session_date не передан
        if "T" in data.start_time:
            session_date = data.start_time.split("T")[0]  # YYYY-MM-DD
        elif " " in data.start_time:
            session_date = data.start_time.split(" ")[0]  # YYYY-MM-DD
        else:
            # Если только время, используем текущую дату
            from datetime import datetime
            session_date = datetime.now().strftime("%Y-%m-%d")
    
    # Извлекаем время из start_time
    if "T" in data.start_time:
        time_part = data.start_time.split("T")[1][:5]  # HH:MM
    elif " " in data.start_time:
        time_part = data.start_time.split(" ")[1][:5]  # HH:MM
    else:
        # Если только время, используем как есть
        time_part = data.start_time[:5]
    
    # Проверка что время действительное (каждые 2 часа: 10, 12, 14, 16, 18, 20, 22)
    valid_times = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
    
    if time_part not in valid_times:
        raise HTTPException(status_code=400, detail=f"Время сеанса должно быть одно из: {valid_times}")
    
    # Проверка что в одном зале в одно время и дату нет других фильмов
    for session in sessions.values():
        if (session.hall_id == data.hall_id and 
            session.start_time == data.start_time and 
            session.session_date == session_date):
            raise HTTPException(status_code=400, detail="В этом зале в это время и дату уже идет фильм")
    
    new_id = max(sessions.keys()) + 1 if sessions else 1
    
    # СОЗДАЕМ КОПИЮ ЗАЛА ДЛЯ ЭТОГО СЕАНСА (важное изменение!)
    session_seats = [
        Seat(row=seat.row, number=seat.number, is_available=True)
        for seat in hall.seats
    ]
    
    from app.models import Session
    session = Session(
        id=new_id,
        movie_title=data.movie_title,
        cinema_id=data.cinema_id,
        hall_id=data.hall_id,
        start_time=time_part,  # Сохраняем только время
        session_date=session_date,  # Сохраняем дату
        price=data.price,
        seats=session_seats  # У КАЖДОГО СЕАНСА СВОИ МЕСТА!
    )
    sessions[new_id] = session
    
    # Сохраняем в файл
    save_sessions()
    
    logger.info(f"Session created: {session}")
    
    # Возвращаем сессию с session_date для фронтенда
    from app.schemas import SessionSchema
    return SessionSchema(
        id=session.id,
        movie_title=session.movie_title,
        cinema_id=session.cinema_id,
        hall_id=session.hall_id,
        start_time=session.start_time,
        session_date=session_date,
        price=session.price
    )

@app.post("/sessions", response_model=SessionSchema)
def create_session(data: CreateSessionSchema):
    """Создать новый сеанс"""
    logger.info(f"POST /sessions - {data.movie_title} в {data.start_time}")
    
    if data.cinema_id not in cinemas:
        raise HTTPException(status_code=400, detail="Cinema not found")
    
    if data.hall_id not in halls:
        raise HTTPException(status_code=400, detail="Hall not found")
    
    # Проверка что зал принадлежит указанному кинотеатру
    hall = halls.get(data.hall_id)
    if hall.cinema_id != data.cinema_id:
        raise HTTPException(status_code=400, detail="Hall does not belong to this cinema")
    
    # Проверка что время действительное (каждые 2 часа: 10, 12, 14, 16, 18, 20, 22)
    valid_times = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
    if data.start_time not in valid_times:
        raise HTTPException(status_code=400, detail=f"Время сеанса должно быть одно из: {valid_times}")
    
    # Проверка что в одном зале в одно время нет других фильмов
    for session in sessions.values():
        if session.hall_id == data.hall_id and session.start_time == data.start_time:
            raise HTTPException(status_code=400, detail="В этом зале в это время уже идет фильм")
    
    new_id = max(sessions.keys()) + 1 if sessions else 1
    
    # Получить места из зала
    session_seats = [
        Seat(row=seat.row, number=seat.number, is_available=True)
        for seat in hall.seats
    ]
    
    from app.models import Session
    session = Session(
        id=new_id,
        movie_title=data.movie_title,
        cinema_id=data.cinema_id,
        hall_id=data.hall_id,
        start_time=data.start_time,
        price=data.price,
        seats=session_seats
    )
    sessions[new_id] = session
    logger.info(f"Session created: {session}")
    
    # Логируем действие администратора
    log_action(
        action="CREATE_SESSION",
        user_id="admin",  # TODO: получить реальный user_id из аутентификации
        details={
            "session_id": session.id,
            "movie_title": session.movie_title,
            "cinema_id": session.cinema_id,
            "hall_id": session.hall_id,
            "start_time": session.start_time,
            "price": session.price
        }
    )
    
    return session


@app.post("/api/session/sessions/multiple", response_model=List[SessionSchema])
def create_multiple_sessions_api(data: CreateMultipleSessionsSchema):
    """Создать несколько сеансов одного фильма"""
    logger.info(f"POST /api/session/sessions/multiple - {data.movie_title}, {len(data.start_times)} сеансов")
    
    if data.cinema_id not in cinemas:
        raise HTTPException(status_code=400, detail="Cinema not found")
    
    if data.hall_id not in halls:
        raise HTTPException(status_code=400, detail="Hall not found")
    
    # Проверка что зал принадлежит указанному кинотеатру
    hall = halls.get(data.hall_id)
    if hall.cinema_id != data.cinema_id:
        raise HTTPException(status_code=400, detail="Hall does not belong to this cinema")
    
    # Проверка что время действительное (каждые 2 часа: 10, 12, 14, 16, 18, 20, 22)
    valid_times = ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"]
    
    created_sessions = []
    
    for start_time in data.start_times:
        # Проверка времени
        if start_time not in valid_times:
            raise HTTPException(status_code=400, detail=f"Время сеанса {start_time} недействительно. Допустимые времена: {valid_times}")
        
        # Проверка что в одном зале в это время нет других фильмов
        for session in sessions.values():
            if session.hall_id == data.hall_id and session.start_time == start_time:
                raise HTTPException(status_code=400, detail=f"В этом зале на время {start_time} уже идет фильм")
        
        new_id = max(sessions.keys()) + 1 if sessions else 1
        
        # СОЗДАЕМ КОПИЮ ЗАЛА ДЛЯ ЭТОГО СЕАНСА
        session_seats = [
            Seat(row=seat.row, number=seat.number, is_available=True)
            for seat in hall.seats
        ]
        
        from app.models import Session
        session = Session(
            id=new_id,
            movie_title=data.movie_title,
            cinema_id=data.cinema_id,
            hall_id=data.hall_id,
            start_time=start_time,
            price=data.price,
            seats=session_seats
        )
        sessions[new_id] = session
        created_sessions.append(session)
    
    # Сохраняем в файл
    save_sessions()
    
    logger.info(f"Created {len(created_sessions)} sessions for movie {data.movie_title}")
    return created_sessions


@app.delete("/api/session/sessions/{session_id}")
def delete_session_api(session_id: int):
    """Удалить сеанс"""
    logger.info(f"DELETE /api/session/sessions/{session_id}")
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    
    # Сохраняем изменения
    save_sessions()
    
    logger.info(f"Session {session_id} deleted")
    
    # Логируем действие администратора
    log_action(
        action="DELETE_SESSION",
        user_id="admin",  # TODO: получить реальный user_id из аутентификации
        details={
            "session_id": session_id,
            "movie_title": session.movie_title,
            "cinema_id": session.cinema_id,
            "hall_id": session.hall_id,
            "start_time": session.start_time
        }
    )
    
    return {"status": "ok", "message": "Session deleted"}

@app.delete("/sessions/{session_id}")
def delete_session(session_id: int):
    """Удалить сеанс"""
    logger.info(f"DELETE /sessions/{session_id}")
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    logger.info(f"Session {session_id} deleted")
    
    # Логируем действие администратора
    log_action(
        action="DELETE_SESSION",
        user_id="admin",  # TODO: получить реальный user_id из аутентификации
        details={
            "session_id": session_id,
            "movie_title": session.movie_title,
            "cinema_id": session.cinema_id,
            "hall_id": session.hall_id,
            "start_time": session.start_time
        }
    )
    
    return {"status": "ok", "message": "Session deleted"}

# Monitoring endpoints
LOG_DIRS = {
    "ticket": "/app/ticket-service/logs",
    "payment": "/app/payment-service/logs",
}

@app.get("/api/monitoring/metrics")
def get_monitoring_metrics():
    """Получить метрики из логов"""
    logger.info("GET /api/monitoring/metrics")
    
    metrics = Counter()
    patterns = {
        "reserved": re.compile(r"reserved|RESERVED"),
        "sold": re.compile(r"sold|SOLD|confirmed"),
        "cancelled": re.compile(r"cancelled|CANCELLED"),
        "payment_success": re.compile(r"Payment successful|SUCCESS"),
        "payment_failed": re.compile(r"Payment failed|FAILED"),
    }
    
    logger.info(f"Checking log directories: {LOG_DIRS}")
    
    for service, path in LOG_DIRS.items():
        logger.info(f"Processing service: {service}, path: {path}")
        if not os.path.exists(path):
            logger.warning(f"Log directory does not exist: {path}")
            continue
            
        logger.info(f"Log directory exists: {path}")
        files = os.listdir(path)
        logger.info(f"Files in directory: {files}")
        
        for file in files:
            file_path = os.path.join(path, file)
            logger.info(f"Processing file: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    line_count = 0
                    for line in f:
                        line_count += 1
                        for key, pattern in patterns.items():
                            if pattern.search(line):
                                metrics[key] += 1
                                logger.debug(f"Found match for {key} in line: {line.strip()}")
                    logger.info(f"Processed {line_count} lines from {file_path}")
            except Exception as e:
                logger.warning(f"Error reading log file {file_path}: {e}")
                continue
    
    logger.info(f"Final metrics: {dict(metrics)}")
    return {
        "reserved": metrics.get("reserved", 0),
        "sold": metrics.get("sold", 0),
        "cancelled": metrics.get("cancelled", 0),
        "payment_success": metrics.get("payment_success", 0),
        "payment_failed": metrics.get("payment_failed", 0),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/monitoring/logs/{service}")
def get_service_logs(service: str, lines: int = 100):
    """Получить последние строки логов для сервиса"""
    logger.info(f"GET /api/monitoring/logs/{service}")
    
    if service not in LOG_DIRS:
        raise HTTPException(status_code=404, detail=f"Service {service} not found")
    
    log_path = LOG_DIRS[service]
    if not os.path.exists(log_path):
        return {"logs": [], "message": f"Log directory for {service} not found"}
    
    all_logs = []
    for file in os.listdir(log_path):
        file_path = os.path.join(log_path, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_logs = f.readlines()
                all_logs.extend(file_logs)
        except Exception as e:
            logger.warning(f"Error reading log file {file_path}: {e}")
            continue
    
    # Возвращаем последние строки
    recent_logs = all_logs[-lines:] if len(all_logs) > lines else all_logs
    
    return {
        "service": service,
        "logs": [log.strip() for log in recent_logs if log.strip()],
        "total_lines": len(recent_logs),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/monitoring/user-actions")
def get_user_actions_logs(limit: int = 100):
    """Получить логи действий пользователей"""
    logger.info(f"GET /api/monitoring/user-actions")
    
    try:
        logs = get_logs(limit)
        return {
            "logs": logs,
            "total_lines": len(logs),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting user actions logs: {e}")
        return {
            "logs": [],
            "total_lines": 0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.delete("/api/monitoring/user-actions/clear")
def clear_user_logs():
    """Очистка всех логов действий пользователей"""
    logger.info("DELETE /api/monitoring/user-actions/clear")
    
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            logger.info("User action logs cleared")
            return {"status": "ok", "message": "Логи успешно очищены"}
        else:
            return {"status": "ok", "message": "Файл логов не найден"}
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при очистке логов")