"""Tests fuer ticket_report.py"""

from datetime import date
from ticket_report import parse_date
from ticket_report import days_open
from ticket_report import load_tickets


def test_parse_date_valid():
    assert parse_date("2026-06-02") == date(2026, 6, 2)


def test_parse_date_empty():
    assert parse_date("") is None


def test_parse_date_whitespace():
    assert parse_date("   ") is None


def test_parse_date_invalid_format():
    assert parse_date("02.06.2026") is None


def test_parse_date_garbage():
    assert parse_date("not a date") is None


def test_parse_date_strips_whitespace():
    assert parse_date("  2026-06-02  ") == date(2026, 6, 2)


def test_days_open_closed_ticket():
    assert days_open(date(2026, 7, 15), date(2026, 8, 1), date(2026, 8, 30)) == 17


def test_days_open_still_open():
    assert days_open(date(2026, 8, 25), None, date(2026, 8, 30)) == 5


def test_days_open_same_day():
    assert days_open(date(2026, 8, 30), date(2026, 8, 30), date(2026, 8, 30)) == 0


def test_days_open_without_created():
    assert days_open(None, None, date(2026, 8, 30)) is None

def test_load_tickets_reads_rows(tmp_path):
    csv_file = tmp_path / "tickets.csv"
    csv_file.write_text(
        "id,phase,days_in_phase\n"
        "T-1,Analysis,10\n"
        "T-2,Closed,3\n",
        encoding="utf-8",
    )
    tickets = load_tickets(str(csv_file))
    assert len(tickets) == 2
    assert tickets[0]["id"] == "T-1"
    assert tickets[1]["days_in_phase"] == "3"


def test_load_tickets_empty_file(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("id,phase,days_in_phase\n", encoding="utf-8")
    assert load_tickets(str(csv_file)) == []