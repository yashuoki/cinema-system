from app.models import Seat, Hall, Session, Cinema

# Инициализация кинотеатров
cinemas = {
    1: Cinema(
        id=1,
        name="Кинотеатр 'Премьера'",
        address="ул. Ленина, д. 25"
    ),
    2: Cinema(
        id=2,
        name="Кинотеатр 'Мир Кино'",
        address="пр. Мира, д. 12"
    ),
    3: Cinema(
        id=3,
        name="Кинотеатр 'Арт-Фильм'",
        address="ул. Советская, д. 8"
    )
}

# Инициализация залов с местами
def create_seats(rows=8, cols=10):
    """Создает матрицу мест: A-Z (rows), 1-N (cols)"""
    seats = []
    for row_idx in range(rows):
        row_letter = chr(ord('A') + row_idx)
        for col_idx in range(1, cols + 1):
            seats.append(Seat(row=row_letter, number=col_idx, is_available=True))
    return seats

# Инициализация залов с местами (распределены по кинотеатрам)
halls = {
    # Кинотеатр 'Премьера'
    1: Hall(
        id=1,
        name="Зал 1 (Малый)",
        cinema_id=1,
        rows=3,
        seats_per_row=10,
        seats=create_seats(3, 10)
    ),
    2: Hall(
        id=2,
        name="Зал 2 (Компактный)",
        cinema_id=1,
        rows=2,
        seats_per_row=12,
        seats=create_seats(2, 12)
    ),
    
    # Кинотеатр 'Мир Кино'
    3: Hall(
        id=3,
        name="Зал 3 (Большой)",
        cinema_id=2,
        rows=5,
        seats_per_row=14,
        seats=create_seats(5, 14)
    ),
    4: Hall(
        id=4,
        name="Зал 4 (Малый)",
        cinema_id=2,
        rows=3,
        seats_per_row=10,
        seats=create_seats(3, 10)
    ),
    
    # Кинотеатр 'Арт-Фильм'
    5: Hall(
        id=5,
        name="Зал 5 (Компактный)",
        cinema_id=3,
        rows=2,
        seats_per_row=12,
        seats=create_seats(2, 12)
    ),
    6: Hall(
        id=6,
        name="Зал 6 (Большой)",
        cinema_id=3,
        rows=5,
        seats_per_row=14,
        seats=create_seats(5, 14)
    )
}

# Инициализация сессий - пустая, будут создаваться через API
sessions = {}

# Отслеживание занятых временных слотов (зал -> время -> True)
occupied_slots = {}