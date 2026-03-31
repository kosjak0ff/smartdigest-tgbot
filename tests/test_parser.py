from smartdigest_bot.fetching.parser import parse_channel_html


def test_parse_channel_html_extracts_posts() -> None:
    html = """
    <div class="tgme_widget_message" data-post="example/123">
      <a class="tgme_widget_message_date" href="https://t.me/example/123">
        <time datetime="2026-03-30T10:00:00+00:00"></time>
      </a>
      <div class="tgme_widget_message_text">Hello <b>world</b><br><br>Second line</div>
    </div>
    """
    posts = parse_channel_html(html)
    assert len(posts) == 1
    assert posts[0].telegram_post_id == 123
    assert posts[0].external_post_url == "https://t.me/example/123"
    assert posts[0].content_text == "Hello\nworld\nSecond line"
    assert posts[0].content_html == "Hello <b>world</b>\n\nSecond line"
    assert posts[0].has_audio is False
    assert posts[0].has_video is False
    assert posts[0].has_photo is False
    assert posts[0].is_forwarded is False


def test_parse_channel_html_marks_audio_posts() -> None:
    html = """
    <div class="tgme_widget_message" data-post="example/124">
      <a class="tgme_widget_message_date" href="https://t.me/example/124">
        <time datetime="2026-03-30T10:00:00+00:00"></time>
      </a>
      <div class="tgme_widget_message_voice_player"></div>
    </div>
    """
    posts = parse_channel_html(html)
    assert len(posts) == 1
    assert posts[0].has_audio is True
    assert posts[0].has_video is False
    assert posts[0].content_text == "[Audio post without text]"
    assert posts[0].content_html == "[Audio post without text]"


def test_parse_channel_html_marks_video_and_forwarded_photo_posts() -> None:
    html = """
    <div class="tgme_widget_message" data-post="example/125">
      <a class="tgme_widget_message_date" href="https://t.me/example/125">
        <time datetime="2026-03-30T10:00:00+00:00"></time>
      </a>
      <div class="tgme_widget_message_forwarded_from">Forwarded from someone</div>
      <a class="tgme_widget_message_photo_wrap" href="#"></a>
      <div class="tgme_widget_message_text">Forwarded caption</div>
    </div>
    <div class="tgme_widget_message" data-post="example/126">
      <a class="tgme_widget_message_date" href="https://t.me/example/126">
        <time datetime="2026-03-30T10:00:00+00:00"></time>
      </a>
      <div class="tgme_widget_message_video_player"></div>
    </div>
    """
    posts = parse_channel_html(html)
    assert len(posts) == 2
    assert posts[0].has_photo is True
    assert posts[0].is_forwarded is True
    assert posts[1].has_video is True
    assert posts[1].content_text == "[Video post without text]"
