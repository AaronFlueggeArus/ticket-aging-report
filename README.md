# Ticket Aging Report

Ein CLI-Tool, das Ticket-Exporte (CSV) auswertet und zeigt, welche offenen
Vorgänge zu lange in ihrer Phase hängen – gruppiert nach Team, Phase oder
beliebiger anderer Spalte.

Entstanden aus einer wiederkehrenden Aufgabe im Problem Management:
Statt wöchentlich in Excel zu filtern und zu sortieren, liefert ein Aufruf
den Überblick.

## Beispiel

```
$ python ticket_report.py sample_data.csv --threshold 14 --group-by solution_responsible

Ticket-Report (Schwelle: 14 Tage)
Gruppiert nach: solution_responsible

Gruppe                      Offen  Auffaellig   Median    Max
-------------------------------------------------------------
Team Alpha                      3           3       89    141
Team Beta                       2           1     32.5     60
Team Gamma                      1           1       20     20
-------------------------------------------------------------
Gesamt                          6           5
```

## Installation

```bash
git clone git@github.com:AaronFlueggeArus/ticket-aging-report.git
cd ticket-aging-report
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Nutzung

```bash
python ticket_report.py <csv-datei> [OPTIONEN]
```

| Option | Standard | Bedeutung |
|---|---|---|
| `--threshold` | `14` | Ab wie vielen Tagen in der Phase ein Ticket als auffällig gilt |
| `--group-by` | `solution_responsible` | Spalte, nach der gruppiert wird |
| `--days-column` | `days_in_phase` | Spalte mit der Phasendauer |
| `--done-column` | `done_date` | Spalte mit dem Abschlussdatum; leer = offen |

Die Spaltennamen sind konfigurierbar, damit das Tool mit Exporten aus
unterschiedlichen Ticketsystemen funktioniert.

## Erwartetes CSV-Format

Mindestens die Spalten, die über die Optionen angesprochen werden.
`sample_data.csv` im Repo zeigt ein vollständiges Beispiel:

```csv
id,creation_time,done_date,phase,substatus,days_in_phase,solution_responsible,defect_severity,prio_systemstability
T-1001,2026-06-02,,Analysis,In Progress,42,Team Alpha,High,1
```

Alle Beispieldaten sind erfunden.

## Tests

```bash
pytest -v
```

31 Tests decken die Logik ab, inklusive Randfälle: leere Datumsfelder,
nicht-numerische Werte, Median bei gerader Anzahl, Schwellwert-Grenze.

## Aufbau

Die Auswertungslogik besteht aus reinen Funktionen ohne Seiteneffekte –
sie nehmen Werte entgegen und geben Werte zurück. Ein- und Ausgabe sind
auf `main()` beschränkt. Dadurch ist die Logik vollständig testbar,
ohne Dateien oder Mocking.

| Funktion | Aufgabe |
|---|---|
| `load_tickets` | CSV einlesen |
| `parse_date` | Datumsstring parsen, `None` bei ungültig |
| `days_open` | Liegedauer berechnen |
| `filter_open` | Nur nicht abgeschlossene Tickets |
| `is_stale` | Schwellwert-Prüfung |
| `group_by` | Gruppierung nach Spalte |
| `summarize` | Kennzahlen je Gruppe |
| `format_report` | Textausgabe erzeugen |