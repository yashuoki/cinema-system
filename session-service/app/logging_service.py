import os
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "user_actions.log"


def log_action(action: str, user_id: str, details: dict = None, ip: str = None):
    """Логирует действия пользователей в файл"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user_id": user_id,
        "ip": ip,
        "details": details or {}
    }
    
    try:
        # Убеждаемся, что директория существует
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Открываем файл в режиме добавления
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Ошибка при логировании: {e}")


def get_logs(limit: int = 100) -> list:
    """Возвращает последние логи"""
    try:
        if not LOG_FILE.exists():
            return []
        
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        logs = []
        for line in lines[-limit:]:
            try:
                logs.append(json.loads(line))
            except:
                pass
        
        return logs
    except Exception as e:
        print(f"Ошибка при чтении логов: {e}")
        return []
