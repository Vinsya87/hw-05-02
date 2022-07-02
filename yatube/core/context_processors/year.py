from datetime import datetime


def year(request) -> int:
    """Добавляет переменную с текущим годом."""
    current_datetime = datetime.now().year
    current_date_month = datetime.now().month
    return {
        "year": int(current_datetime),
        "month": int(current_date_month),
    }
