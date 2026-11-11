# OSNT

Marktbeobachtung für **Data Platforms & KI im öffentlichen Sektor** — Kunden, Projekte, Personen — ohne LinkedIn-Scraper.

Zielunternehmen: Accenture, Deloitte, Capgemini, BearingPoint, T-Systems, ]init[, Bechtle, PwC.

## Kurzantwort: so kommen die Daten möglichst billig

LinkedIn selbst zum Scrapen ist der teuerste Weg (ToS-Verstoß, Account-Sperre, DSGVO, 2025 hat LinkedIn Proxycurl verklagt und der Dienst wurde eingestellt). Die offizielle LinkedIn-API kann **keine** Posts fremder Berater durchsuchen.

| Frage | Günstigste legale Quelle | Kosten |
| --- | --- | --- |
| Welche Kunden, welche Projekte, welches Volumen? | [TED Search API](https://ted.europa.eu/de/simap/developers-corner-for-reusers) + [oeffentlichevergabe.de](https://oeffentlichevergabe.de) (OCDS, auch unter EU-Schwelle) | **0 €** |
| Wie viele Menschen je Firma / Skill? | LinkedIn **Sales Navigator Core**, gespeicherte Suche, CSV hier importieren | **1.088,88 €/Jahr** (Listenpreis Core, Stand 2026, zzgl. MwSt.) |
| Öffentliche Projekterwähnungen / manche Posts | Google über Serper o. ä. (`site:linkedin.com/posts …`), Presse-RSS der Firmen | **0–10 €/Monat** |
| Roh-Posts in großem Volumen | Kommerzielle Datendienste (z. B. Bright Data ~1,30–1,50 USD / 1.000 Records) | nur nach Rechtsprüfung |

**Empfohlene Stufe 1 (diese Anwendung):** TED + Vergabe, 0 €. Das beantwortet für den Public Sector Kunden und Projekte besser als Social Posts, weil Zuschläge, CPV-Codes und oft Auftragswerte enthalten sind.

Live-Stichprobe TED (Deutschland, CPV 72/48, Stand Abruf 2026-11-11): Accenture 66, Deloitte 91, Capgemini 53, BearingPoint 62, T-Systems 107, Bechtle 333, PwC 53, ]init[ 62 IT-Vergaben. Davon nur ein kleiner Teil mit KI-/Datenplattform-Wörtern in der Bekanntmachung — deshalb taggt OSNT den Text zusätzlich.

## Was OSNT bewusst nicht tut

- Kein Login bei LinkedIn
- Keine Cookies, Residential Proxies, Fake-Accounts, Browser-Automation gegen linkedin.com
- Kein Umgehen von Captchas oder Rate-Limits

Personen kommen nur aus einem **CSV, das Sie selbst aus Sales Navigator / Recruiter exportiert haben**, oder später aus namentlichen Nennungen in Presse/Vergabe.

Datenschutz: Personenbezogene LinkedIn-Profile unterliegen der DSGVO (Art. 6 Abs. 1 lit. f, Art. 14, Verzeichnis von Verarbeitungstätigkeiten). Vor Produktivbetrieb mit Personenimport die Datenschutzstelle einbinden.

## Anwendung

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
osnt seed-demo
osnt serve
```

UI: <http://127.0.0.1:8000>

- **Demo laden** — mitgelieferter TED-Ausschnitt (öffentliche Bekanntmachungen)
- **TED live** — aktuelle Zuschläge der acht Firmen in DE, CPV 72/48
- **Vergabe 1 Tag** — letzter verfügbarer Tag von oeffentlichevergabe.de, gefiltert auf die acht Firmen
- **Personen-CSV** — Sales-Navigator-Export (`First Name, Last Name, Company, Title`) oder `data/sample/people.csv`

```bash
osnt sync-ted --limit 50
osnt sync-vergabe --days 1
pytest
```

## Architektur

```
Browser  →  FastAPI (osnt.web)
                │
                ├─ TED Search API          Kunden, Projekte, Werte
                ├─ oeffentlichevergabe.de  Unterschwellen-Vergaben
                ├─ SQLite                  notices, people, ingest_runs
                └─ CSV-Import              Personen (Sales Navigator)
```

Klassifikation (`osnt.classify`): CPV 48/72 = IT; Wörter wie „künstliche Intelligenz“, „Datenplattform“, Databricks, Azure, … = Fokus; Lizenz-/Hardware-Texte = Reseller (häufig Bechtle).

Nächster Ausbau, bewusst getrennt: RSS der Firmenpresse, optional Serper für Google-indexierte Seiten, optional kommerzielle People-API. Kein Scraper-Modul.

## Rechtlicher Rahmen (kurz)

- TED und der Bekanntmachungsservice sind Open Data / amtliche Veröffentlichung.
- LinkedIn User Agreement verbietet Scraping ausdrücklich; US-Verfahren hiQ und die Proxycurl-Klage 2025 zeigen, dass LinkedIn das durchsetzt.
- Die Community Management API ist kostenlos, aber nur für **eigene** Pages/Mitglieder nach OAuth — nicht für Wettbewerbsbeobachtung fremder Feeds.
