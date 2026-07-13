"""Pure-Python calculation utilities for creator fit scoring.

No network or database access — all computation is local.
"""


def estimated_rate(creator: dict) -> float:
    """Estimate creator rate as follower_count * 0.5.

    Returns 0.0 when follower_count is missing, None, or zero/negative.
    """
    followers = creator.get("follower_count") or 0
    return followers * 0.5 if followers > 0 else 0.0


def calculate_engagement_rate(
    followers: int | float, avg_likes: int | float, avg_comments: int | float
) -> float:
    """Return engagement rate as a percentage: (likes + comments) / followers * 100.

    Returns 0.0 when followers is zero or missing to avoid division by zero.
    """
    if not followers:
        return 0.0
    return ((avg_likes + avg_comments) / followers) * 100


def calculate_reach_ratio(
    avg_reel_views: int | float, followers: int | float
) -> float:
    """Return reach ratio: avg_reel_views / followers.

    Returns 0.0 when followers is zero or missing.
    """
    if not followers:
        return 0.0
    return avg_reel_views / followers


def calculate_fit_score(creator: dict, brief: dict) -> float:
    """Weighted fit score between 0.0 and 1.0.

    Scoring rubric (total 100 points, divided by 100):
      - niche_match:      25 pts — exact niche match
      - language_match:   20 pts — language in brief targets or vice-versa
      - region_match:     20 pts — exact region match
      - budget_fit:       15 pts — estimated rate within budget_max
      - brand_experience:  10 pts — creator has prior brand work
      - engagement_rate:   5 pts — engagement rate >= 3.0%
      - reach_ratio:       5 pts — reach ratio >= 3.0
    """
    scores = 0

    # niche match — 25 pts
    if creator.get("detected_niche") == brief.get("product_category"):
        scores += 25

    # language match — 20 pts
    c_lang = creator.get("detected_language") or ""
    b_langs = brief.get("target_language") or []
    if isinstance(b_langs, str):
        b_langs = [b_langs]
    if c_lang in b_langs or b_langs in (c_lang,):
        scores += 20

    # region match — 20 pts
    if creator.get("detected_region") == brief.get("target_location"):
        scores += 20

    # budget fit — 15 pts
    rate = estimated_rate(creator)
    if brief.get("budget_max", 0) >= rate:
        scores += 15

    # brand experience — 10 pts
    if creator.get("has_brand_experience"):
        scores += 10

    # engagement rate — 5 pts
    eng = calculate_engagement_rate(
        creator.get("follower_count", 0),
        creator.get("avg_likes", 0),
        creator.get("avg_comments", 0),
    )
    if eng >= 3.0:
        scores += 5

    # reach ratio — 5 pts
    reach = calculate_reach_ratio(
        creator.get("avg_reel_views", 0),
        creator.get("follower_count", 0),
    )
    if reach >= 3.0:
        scores += 5

    return scores / 100.0