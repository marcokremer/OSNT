from __future__ import annotations

# List prices checked 2026-11. USD as published; EUR ≈ 0.92 for display.

PROVIDERS = (
    {
        "id": "apify-post-search",
        "label": "Apify HarvestAPI — Post Search",
        "best_for": "Direkt Posts zu KI/Datenplattform + Public Sector je Firma",
        "usd_per_1k_posts": 2.0,
        "usd_per_1k_people": 0.0,
        "notes": "authorsCompanies + Suchbegriffe. Keine Cookies. Günstigster Weg zu den Posts.",
    },
    {
        "id": "brightdata",
        "label": "Bright Data LinkedIn Scraper API",
        "best_for": "Personen suchen, dann Posts je Profil-URL",
        "usd_per_1k_posts": 1.5,
        "usd_per_1k_people": 1.5,
        "notes": "5.000 Records/Monat gratis. Danach 1,50 USD / 1.000 erfolgreiche Records.",
    },
    {
        "id": "apify-people-then-posts",
        "label": "Apify — Profile Search + Profile Posts",
        "best_for": "Zuerst Köpfe zählen, dann deren Feed",
        "usd_per_1k_posts": 2.0,
        "usd_per_1k_people": 4.0,
        "notes": "Teurer als Post-Search, aber saubere Personenzahl.",
    },
    {
        "id": "serper",
        "label": "Google/Serper site:linkedin.com/posts",
        "best_for": "Stichprobe indexierter Posts, ohne LinkedIn-Session",
        "usd_per_1k_posts": 0.3,
        "usd_per_1k_people": 0.0,
        "notes": "Nur was Google kennt. Unvollständig, aber Pfennigbeträge.",
    },
)


def estimate(
    people: int = 400,
    posts_per_person: int = 12,
    post_search_hits: int = 1600,
) -> dict:
    """Cost model for this exact OSINT question, not a generic scraper."""
    posts = people * posts_per_person
    rows = []
    for provider in PROVIDERS:
        if provider["id"] == "apify-post-search":
            usd = post_search_hits / 1000 * provider["usd_per_1k_posts"]
            volume = f"{post_search_hits} Posts (Suche, nicht alle Feeds)"
        elif provider["id"] == "serper":
            searches = 80
            usd = searches / 1000 * 1.0
            volume = f"{searches} Google-Suchen"
        else:
            usd = (
                people / 1000 * provider["usd_per_1k_people"]
                + posts / 1000 * provider["usd_per_1k_posts"]
            )
            volume = f"{people} Profile + {posts} Posts"
        rows.append(
            {
                **provider,
                "usd": round(usd, 2),
                "eur": round(usd * 0.92, 2),
                "volume": volume,
            }
        )
    rows.sort(key=lambda r: r["usd"])
    return {
        "assumptions": {
            "people": people,
            "posts_per_person": posts_per_person,
            "posts": posts,
            "post_search_hits": post_search_hits,
            "companies": 8,
            "note": "DE, Data/AI, Public Sector — grobe Nische, keine LinkedIn-Volkszählung",
        },
        "cheapest": rows[0],
        "providers": rows,
        "not_offered": {
            "diy_linkedin_login": "Kein Cookie-/Playwright-Scraper gegen linkedin.com (ToS, Account-Sperre, Proxycurl-Klage 2025).",
            "official_api": "Community Management API sieht nur die eigene Page, nicht Wettbewerber-Feeds.",
        },
    }
