from __future__ import annotations

from pathlib import Path

import pytest

import apple_spyder.settings as settings
from apple_spyder.settings import ConfigError


@pytest.fixture(autouse=True)
def reset_settings_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "CONFIG_PATH", tmp_path / "config.yaml")
    settings._app_config_cache = None
    yield
    settings._app_config_cache = None


def write_config(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_config_with_bark_section() -> None:
    write_config(
        settings.CONFIG_PATH,
        """
weibo:
  enabled: false
  app_key: app_key
  app_secret: app_secret
  redirect_uri: https://example.com/callback
  access_token: token
  real_ip: 127.0.0.1
telegram:
  enabled: true
  bot_token: 123456:test_token
  chat_ids:
    - 10001
bark:
  enabled: true
  server_url: https://example.com
  device_key: bark_key
  username: admin
  password: secret
urls:
  apple_developer_rss: https://developer.apple.com/news/releases/rss/releases.rss
web:
  enabled: false
  host: 127.0.0.1
  port: 5005
scheduler:
  enabled: true
  cron_expr: '*/30 * * * *'
  run_on_startup: true
""".strip(),
    )

    config = settings.get_app_config()

    assert config.bark.enabled is True
    assert config.bark.server_url == "https://example.com"
    assert config.bark.device_key == "bark_key"
    assert config.bark.username == "admin"
    assert config.bark.password == "secret"


def test_bark_requires_http_url_when_enabled() -> None:
    write_config(
        settings.CONFIG_PATH,
        """
weibo:
  enabled: false
  app_key: app_key
  app_secret: app_secret
  redirect_uri: https://example.com/callback
  access_token: token
  real_ip: 127.0.0.1
telegram:
  enabled: true
  bot_token: 123456:test_token
  chat_ids:
    - 10001
bark:
  enabled: true
  server_url: bark-worker.sakuraelysia.workers.dev
  device_key: bark_key
  username: admin
  password: secret
urls:
  apple_developer_rss: https://developer.apple.com/news/releases/rss/releases.rss
web:
  enabled: false
  host: 127.0.0.1
  port: 5005
scheduler:
  enabled: true
  cron_expr: '*/30 * * * *'
  run_on_startup: true
""".strip(),
    )

    with pytest.raises(ConfigError, match="bark.server_url"):
        settings.get_app_config()
