from osnt.costs import estimate


def test_post_search_is_cheapest_for_this_niche():
    result = estimate(people=400, posts_per_person=12, post_search_hits=1600)
    assert result["cheapest"]["id"] in {"apify-post-search", "serper"}
    assert result["cheapest"]["usd"] < 20
    ids = {row["id"] for row in result["providers"]}
    assert "apify-post-search" in ids
    assert "brightdata" in ids
