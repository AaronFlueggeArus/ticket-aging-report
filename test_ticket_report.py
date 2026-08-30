"""Tests fuer ticket_report.py"""

from datetime import date

from ticket_report import parse_date


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