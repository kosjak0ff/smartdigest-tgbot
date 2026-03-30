from smartdigest_bot.bootstrap.first_run import select_first_run_posts
from smartdigest_bot.models import ParsedPost


def _post(post_id: int) -> ParsedPost:
    return ParsedPost(
        telegram_post_id=post_id,
        external_post_url=f"https://t.me/example/{post_id}",
        content_text=f"Post {post_id}",
        published_at=None,
        author_name=None,
        raw_html=None,
    )


def test_first_run_mark_seen_skips_delivery() -> None:
    assert select_first_run_posts([_post(1), _post(2)], mode="mark_seen", max_posts=0) == []


def test_first_run_send_recent_respects_limit() -> None:
    selected = select_first_run_posts([_post(1), _post(2), _post(3)], mode="send_recent", max_posts=2)
    assert [item.telegram_post_id for item in selected] == [2, 3]
