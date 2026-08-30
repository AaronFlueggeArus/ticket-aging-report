"""Aging- und Eskalations-Report fuer Ticket-Exporte (CSV)."""

import csv
from datetime import date, datetime
from statistics import median


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

def load_tickets(path: str) -> list[dict]:
    """Liest eine Ticket-CSV ein und gibt die Zeilen als Dicts zurueck.

    Erwartet eine Kopfzeile mit Spaltennamen.
    """
    with open(path, newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))

def filter_open(tickets: list[dict], done_column: str = "done_date") -> list[dict]:
    """Gibt nur die Tickets zurueck, die noch nicht abgeschlossen sind.

    Als offen gilt ein Ticket, dessen Done-Spalte leer ist.
    """
    return [t for t in tickets if not t.get(done_column, "").strip()]


def is_stale(ticket: dict, threshold: int, days_column: str = "days_in_phase") -> bool:
    """Prueft, ob ein Ticket laenger als threshold Tage in seiner Phase haengt.

    Nicht lesbare oder fehlende Werte gelten als nicht auffaellig.
    """
    try:
        days = int(ticket.get(days_column, "").strip())
    except (ValueError, AttributeError):
        return False
    return days >= threshold

def group_by(tickets: list[dict], column: str) -> dict[str, list[dict]]:
    """Gruppiert Tickets nach dem Wert einer Spalte.

    Leere oder fehlende Werte landen unter "(leer)".
    """
    groups: dict[str, list[dict]] = {}
    for ticket in tickets:
        key = ticket.get(column, "").strip() or "(leer)"
        groups.setdefault(key, []).append(ticket)
    return groups


def summarize(tickets: list[dict], days_column: str = "days_in_phase") -> dict:
    """Berechnet Kennzahlen ueber eine Menge von Tickets.

    Nicht lesbare Tagewerte werden uebersprungen.
    """
    values = []
    for ticket in tickets:
        try:
            values.append(int(ticket.get(days_column, "").strip()))
        except (ValueError, AttributeError):
            continue

    if not values:
        return {"count": len(tickets), "median_days": None, "max_days": None}

    return {
        "count": len(tickets),
        "median_days": median(values),
        "max_days": max(values),
    }