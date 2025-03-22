from datetime import datetime, timedelta, timezone


def get_quito_time() -> datetime:
    """Función para obtener la hora actual en Quito, Ecuador."""
    quito_timezone = timezone(timedelta(hours=-5))
    return datetime.now(quito_timezone)
