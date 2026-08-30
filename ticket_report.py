"""Aging- und Eskalations-Report fuer Ticket-Exporte (CSV)."""

from datetime import date, datetime


def parse_date(value: str) -> date | None:
    """Wandelt einen ISO-Datumsstring in ein date-Objekt um.

    Gibt None zurueck, wenn der Wert leer oder ungueltig ist.
    """
    if not value or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

def days_open(created: date | None, done: date | None, today: date) -> int | None:
    """Berechnet, wie viele Tage ein Ticket offen war bzw. ist.

    Ist done gesetzt, zaehlt der Zeitraum bis zum Abschluss.
    Sonst bis today. Ohne created ist keine Aussage moeglich: None.
    """
    if created is None:
        return None
    end = done if done is not None else today
    return (end - created).days    