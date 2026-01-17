import requests
from app.logger import logger

SESSION_SERVICE_URL = "http://session-service:8000"


def check_seat_available(session_id: int, row: str, number: int) -> bool:
    """Проверить доступность места"""
    try:
        url = f"{SESSION_SERVICE_URL}/sessions/{session_id}/seats"
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        seats = response.json()

        for seat in seats:
            if seat["row"] == row and seat["number"] == number:
                return seat["is_available"]

        return False

    except Exception as e:
        logger.error(f"Session Service unavailable: {e}")
        return False


def mark_seat_as_reserved(session_id: int, row: str, number: int) -> bool:
    """Отметить место как зарезервированное"""
    try:
        url = f"{SESSION_SERVICE_URL}/sessions/{session_id}/seats/{row}/{number}"
        response = requests.put(
            url,
            json={"is_available": False},
            timeout=3
        )
        response.raise_for_status()
        logger.info(f"Seat {row}{number} marked as reserved")
        return True
    except Exception as e:
        logger.error(f"Failed to mark seat as reserved: {e}")
        return False


def mark_seat_as_available(session_id: int, row: str, number: int) -> bool:
    """Отметить место как доступное"""
    try:
        url = f"{SESSION_SERVICE_URL}/sessions/{session_id}/seats/{row}/{number}"
        response = requests.put(
            url,
            json={"is_available": True},
            timeout=3
        )
        response.raise_for_status()
        logger.info(f"Seat {row}{number} marked as available")
        return True
    except Exception as e:
        logger.error(f"Failed to mark seat as available: {e}")
        return False