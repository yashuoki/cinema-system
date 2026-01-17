from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import NotificationRequest
from app.logger import logger
from typing import List
from datetime import datetime
import json

app = FastAPI(
    title="Notification Service",
    docs_url="/docs"
)

# CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище уведомлений
notifications = []


@app.on_event("startup")
def startup():
    logger.info("Notification Service started")


@app.post("/notify")
def send_notification(request: NotificationRequest):
    """Отправить уведомление"""
    
    # Подготовить сообщение в зависимости от типа события
    if request.event_type == "purchase":
        subject = "Билет успешно куплен! 🎬"
        body = f"Ваш билет #{request.ticket_id} успешно оплачен и отправлен на почту."
    elif request.event_type == "cancellation":
        subject = "Билет отменён ❌"
        body = f"Ваш билет #{request.ticket_id} был отменён."
    elif request.event_type == "refund":
        subject = "Возврат средств ✅"
        body = f"По вашему билету #{request.ticket_id} произведён возврат денег на карту."
    else:
        subject = "Уведомление"
        body = request.message
    
    logger.info(
        f"Notification for ticket {request.ticket_id}: {subject}"
    )
    
    if request.email:
        logger.info(f"Email would be sent to: {request.email}")
    
    notification = {
        "ticket_id": request.ticket_id,
        "email": request.email,
        "event_type": request.event_type,
        "subject": subject,
        "message": body,
        "status": "DELIVERED",
        "timestamp": datetime.now().isoformat()
    }
    
    notifications.append(notification)
    return {"status": "DELIVERED", "message": subject}


@app.get("/notifications")
def get_notifications():
    """Получить все уведомления"""
    logger.info("GET /notifications")
    return notifications