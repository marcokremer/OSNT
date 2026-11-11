# OSNT

LinkedIn-OSINT als Webanwendung: **Posts** von Leuten bei Accenture, Deloitte, Capgemini, BearingPoint, T-Systems, ]init[, Bechtle und PwC, die **Data Platforms / KI** mit **Public-Sector-Kunden** machen.

Aus den Posts: wie viele Menschen, welche Kunden, welche Projekte.

## Scraper — ohne LinkedIn-Login

OSNT steuert fertige LinkedIn-Scraper-APIs an (HarvestAPI über Apify, optional Bright Data, optional Google). Es loggt sich nicht bei LinkedIn ein, setzt keine Cookies und steuert linkedin.com nicht per Browser.

Der **günstigste** Weg zu *genau diesen* Posts ist nicht „alle Mitarbeiter scrapen“, sondern **Post-Suche** mit Firmenfilter:

| Weg | Was passiert | Grobe Kosten für diese Nische |
| --- | --- | --- |
| **Apify HarvestAPI Post Search** | `authorsCompanies` = die acht Firmen, Queries = Datenplattform / KI / öffentlicher Sektor / ITZBund | **~3 USD** bei ~1.600 Posts (2 USD / 1.000) |
| Bright Data | Personen + Posts, 1,50 USD / 1.000 Records, 5.000/Monat gratis | ~12 USD bei 400 Profilen + 4.800 Posts |
| Apify Profile Search + Profile Posts | Zuerst Köpfe, dann Feeds | ~18 USD |
| Serper `site:linkedin.com/posts` | Nur von Google indexierte Snippets | **< 1 USD**, unvollständig |
| Offizielle LinkedIn-API | Sieht nur die eigene Page | 0 €, unbrauchbar für Wettbewerber |
| Eigenes Playwright + Cookies | nicht implementiert | ToS, Account tot, Proxycurl 2025 |

Annahme im Rechner (`osnt costs` / Tab Kosten): 8 Firmen, ~400 Köpfe in der Nische, 12 Posts/Person **oder** 1.600 Post-Search-Treffer. Keine LinkedIn-Volkszählung.

**Praktisch:** `APIFY_TOKEN` setzen, in der UI „Apify scrapen“. Ohne Token läuft die Demo (synthetische Posts, klar als Demo gekennzeichnet).

## Start

```bash
pip install -e ".[dev]"
osnt seed-demo
osnt serve
```

http://127.0.0.1:8000 — Tabs Posts, Personen, Kunden, Projekte, Kosten.

```bash
export APIFY_TOKEN=...          # HarvestAPI
osnt scrape --provider apify --max-posts 40
osnt costs
pytest
```

## Pipeline

1. Post-Search (oder Demo) für die acht Firmen und die Fokus-Queries in `osnt/queries.py`
2. Autor → Person, Text → Tags (KI / Datenplattform / Public Sector)
3. Gazetteer → Kunden (ITZBund, BMI, BKA, DRV, byte Bayern, …)
4. Muster → Projektnamen (Projekt X, Rahmenvertrag Y, Einführung Z)
5. Person zählt, wenn Headline oder Posts beides haben: Data/AI **und** Public Sector

Kein TED-Dashboard. Vergabedaten beantworten eine andere Frage (Zuschlag), nicht „was posten die Berater“.
