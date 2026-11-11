"""LinkedIn post-search queries for this exact market slice."""

from osnt.companies import COMPANIES

# HarvestAPI allows ~5 boolean operators per query. Keep them short.
POST_SEARCH_QUERIES = (
    "Datenplattform OR \"Data Platform\" OR Data Lake",
    "\"künstliche Intelligenz\" OR GenAI OR \"machine learning\"",
    "\"öffentlicher Sektor\" OR \"öffentliche Verwaltung\" OR \"Public Sector\"",
    "ITZBund OR \"Onlinezugangsgesetz\" OR OZG",
    "KI Verwaltung OR \"AI government\" OR GovTech",
)

AUTHOR_COMPANIES = tuple(name for c in COMPANIES for name in c.search_names)


def apify_post_search_input(max_posts: int = 50) -> dict:
    return {
        "searchQueries": list(POST_SEARCH_QUERIES),
        "authorsCompanies": list(AUTHOR_COMPANIES),
        "maxPosts": max_posts,
        "postedLimit": "year",
    }


def brightdata_company_post_input() -> list[dict]:
    return [{"url": c.linkedin_company} for c in COMPANIES]


def serper_queries() -> list[str]:
    queries = []
    for company in COMPANIES:
        queries.append(
            f'site:linkedin.com/posts "{company.label}" (Datenplattform OR KI OR "künstliche Intelligenz") (Verwaltung OR "öffentlicher Sektor" OR ITZBund)'
        )
    return queries
