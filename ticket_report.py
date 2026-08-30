"""Aging- und Eskalations-Report fuer Ticket-Exporte (CSV)."""

import argparse
import csv
import sys
from datetime import date, datetime
from statistics import median

# Spaltenbreiten des Reports: Gruppe, Offen, Auffaellig, Median, Max
COLUMN_WIDTHS = (25, 8, 12, 9, 7)
LINE_WIDTH = sum(COLUMN_WIDTHS)


def cell(ticket: dict, column: str) -> str:
    """Liest eine Zelle als bereinigten String.

    Fehlende Spalten und None-Werte werden zu "". csv.DictReader liefert
    None, wenn eine Zeile weniger Felder hat als die Kopfzeile.
    """
    return (ticket.get(column) or "").strip()


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

    Ist done gesetzt, zaehlt der Zeitraum bis zum Abschluss, sonst bis today.
    Ohne created oder bei negativem Zeitraum (Datenfehler): None.
    """
    if created is None:
        return None
    end = done if done is not None else today
    days = (end - created).days
    return days if days >= 0 else None


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
    return [t for t in tickets if not cell(t, done_column)]


def ticket_age(
    ticket: dict,
    today: date,
    days_column: str = "days_in_phase",
    created_column: str = "creation_time",
    done_column: str = "done_date",
) -> int | None:
    """Ermittelt die Liegedauer eines Tickets in Tagen.

    Bevorzugt die Spalte mit der Phasendauer. Fehlt sie oder ist sie
    nicht lesbar, wird aus Erstell- und Abschlussdatum gerechnet.
    Gibt None zurueck, wenn beides nicht moeglich ist.
    """
    try:
        return int(cell(ticket, days_column))
    except ValueError:
        pass

    created = parse_date(cell(ticket, created_column))
    done = parse_date(cell(ticket, done_column))
    return days_open(created, done, today)


def is_stale(age: int | None, threshold: int) -> bool:
    """Prueft, ob eine Liegedauer die Schwelle erreicht.

    Nicht ermittelbare Dauern gelten als nicht auffaellig.
    """
    if age is None:
        return False
    return age >= threshold


def group_by(tickets: list[dict], column: str) -> dict[str, list[dict]]:
    """Gruppiert Tickets nach dem Wert einer Spalte.

    Leere oder fehlende Werte landen unter "(leer)".
    """
    groups: dict[str, list[dict]] = {}
    for ticket in tickets:
        key = cell(ticket, column) or "(leer)"
        groups.setdefault(key, []).append(ticket)
    return groups


def summarize(ages: list[int | None]) -> dict:
    """Berechnet Kennzahlen ueber eine Liste von Liegedauern.

    Nicht ermittelbare Werte fliessen nicht in Median und Max ein,
    zaehlen aber bei count mit.
    """
    values = [a for a in ages if a is not None]

    if not values:
        return {"count": len(ages), "median_days": None, "max_days": None}

    med = median(values)
    return {
        "count": len(ages),
        "median_days": int(med) if med == int(med) else round(med, 1),
        "max_days": max(values),
    }


def build_summary(
    tickets: list[dict],
    threshold: int,
    group_column: str,
    today: date,
    days_column: str = "days_in_phase",
    created_column: str = "creation_time",
    done_column: str = "done_date",
) -> dict[str, dict]:
    """Fasst Tickets pro Gruppe zusammen und ergaenzt die Anzahl auffaelliger."""
    result = {}
    for name, group in group_by(tickets, group_column).items():
        ages = [
            ticket_age(t, today, days_column, created_column, done_column)
            for t in group
        ]
        stats = summarize(ages)
        stats["stale_count"] = sum(1 for a in ages if is_stale(a, threshold))
        result[name] = stats
    return result


def format_report(
    groups: dict[str, dict],
    threshold: int,
    group_column: str,
) -> str:
    """Formatiert die Auswertung als mehrzeiligen Text.

    Erwartet pro Gruppe ein Dict mit den Schluesseln
    count, stale_count, median_days und max_days.
    """
    w_group, w_open, w_stale, w_median, w_max = COLUMN_WIDTHS

    lines = [
        f"Ticket-Report (Schwelle: {threshold} Tage)",
        f"Gruppiert nach: {group_column}",
        "",
        f"{'Gruppe':<{w_group}}"
        f"{'Offen':>{w_open}}"
        f"{'Auffaellig':>{w_stale}}"
        f"{'Median':>{w_median}}"
        f"{'Max':>{w_max}}",
        "-" * LINE_WIDTH,
    ]

    for name in sorted(groups):
        data = groups[name]
        median_text = "-" if data["median_days"] is None else str(data["median_days"])
        max_text = "-" if data["max_days"] is None else str(data["max_days"])
        lines.append(
            f"{name[: w_group - 1]:<{w_group}}"
            f"{data['count']:>{w_open}}"
            f"{data['stale_count']:>{w_stale}}"
            f"{median_text:>{w_median}}"
            f"{max_text:>{w_max}}"
        )

    total = sum(g["count"] for g in groups.values())
    total_stale = sum(g["stale_count"] for g in groups.values())
    lines.append("-" * LINE_WIDTH)
    lines.append(f"{'Gesamt':<{w_group}}{total:>{w_open}}{total_stale:>{w_stale}}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aging-Report ueber einen Ticket-Export (CSV)."
    )
    parser.add_argument("csv_file", help="Pfad zur CSV-Datei")
    parser.add_argument(
        "--threshold",
        type=int,
        default=14,
        help="Ab wie vielen Tagen in der Phase ein Ticket auffaellig ist (Standard: 14)",
    )
    parser.add_argument(
        "--group-by",
        default="solution_responsible",
        help="Spalte, nach der gruppiert wird (Standard: solution_responsible)",
    )
    parser.add_argument(
        "--days-column",
        default="days_in_phase",
        help="Spalte mit der Phasendauer (Standard: days_in_phase)",
    )
    parser.add_argument(
        "--created-column",
        default="creation_time",
        help="Spalte mit dem Erstelldatum (Standard: creation_time)",
    )
    parser.add_argument(
        "--done-column",
        default="done_date",
        help="Spalte mit dem Abschlussdatum (Standard: done_date)",
    )
    args = parser.parse_args()

    try:
        tickets = load_tickets(args.csv_file)
    except FileNotFoundError:
        print(f"Datei nicht gefunden: {args.csv_file}", file=sys.stderr)
        sys.exit(1)

    open_tickets = filter_open(tickets, args.done_column)
    summary = build_summary(
        open_tickets,
        args.threshold,
        args.group_by,
        date.today(),
        args.days_column,
        args.created_column,
        args.done_column,
    )
    print(format_report(summary, args.threshold, args.group_by))


if __name__ == "__main__":
    main()