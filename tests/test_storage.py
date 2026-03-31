from smartdigest_bot.models import ChannelConfig, ParsedPost
from smartdigest_bot.storage.channels_repo import ChannelsRepository
from smartdigest_bot.storage.db import connect
from smartdigest_bot.storage.deliveries_repo import DeliveriesRepository
from smartdigest_bot.storage.migrations import migrate
from smartdigest_bot.storage.posts_repo import PostsRepository


def test_storage_saves_posts_and_delivery(tmp_path) -> None:
    connection = connect(str(tmp_path / "test.sqlite3"))
    migrate(connection)
    channels_repo = ChannelsRepository(connection)
    posts_repo = PostsRepository(connection)
    deliveries_repo = DeliveriesRepository(connection)

    channels_repo.sync([ChannelConfig(username="example", title="Example")])
    channel = channels_repo.list_active()[0]
    stored = posts_repo.upsert_post(
        channel_id=channel["id"],
        channel_username="example",
        post=ParsedPost(
            telegram_post_id=1,
            external_post_url="https://t.me/example/1",
            content_text="Hello",
            content_html="Hello",
            published_at=None,
            author_name=None,
            has_audio=True,
            has_video=False,
            has_photo=True,
            is_forwarded=True,
            raw_html="<div></div>",
        ),
    )
    assert stored.has_audio is True
    assert stored.has_video is False
    assert stored.has_photo is True
    assert stored.is_forwarded is True
    assert stored.content_html == "Hello"
    assert deliveries_repo.is_delivered(stored.id) is False
    deliveries_repo.mark_delivered(stored.id, "-1001", None, 42)
    assert deliveries_repo.is_delivered(stored.id) is True
