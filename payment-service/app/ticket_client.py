import requests
from app.logger import logger

TICKET_SERVICE_URL = "http://ticket-service:8001"


def confirm_ticket(ticket_id: int):
    try:
        url = f"{TICKET_SERVICE_URL}/tickets/confirm/{ticket_id}"
        response = requests.post(url, timeout=3)
        response.raise_for_status()
        logger.info(f"Ticket {ticket_id} confirmed")
    except Exception as e:
        logger.error(f"Failed to confirm ticket {ticket_id}: {e}")


def cancel_ticket(ticket_id: int):
    try:
        url = f"{TICKET_SERVICE_URL}/tickets/cancel/{ticket_id}"
        response = requests.post(url, timeout=3)
        response.raise_for_status()
        logger.info(f"Ticket {ticket_id} cancelled")
    except Exception as e:
        logger.error(f"Failed to cancel ticket {ticket_id}: {e}")


NOTIFICATION_SERVICE_URL = "http://notification-service:8003"


def notify(ticket_id: int, event_type: str = "purchase", email: str = None):
    try:
        url = f"{NOTIFICATION_SERVICE_URL}/notify"
        
        messages = {
            "purchase": "Билет успешно оплачен и подтверждён",
            "cancellation": "Билет отменён",
            "refund": "Деньги возвращены на карту"
        }
        
        payload = {
            "ticket_id": ticket_id,
            "message": messages.get(event_type, "Обновление статуса билета"),
            "event_type": event_type,
            "email": email
        }
        response = requests.post(url, json=payload, timeout=3)
        response.raise_for_status()
        logger.info(f"Notification triggered for ticket {ticket_id}, event: {event_type}")
    except Exception as e:
        logger.error(f"Failed to notify for ticket {ticket_id}: {e}")