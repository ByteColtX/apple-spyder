from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from croniter import croniter

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
TEMPLATES_DIR = ROOT_DIR / "templates"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
DATABASE_PATH = DATA_DIR / "apple-spyder.db"


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class WeiboConfig:
    enabled: bool
    app_key: str
    app_secret: str
    redirect_uri: str
    access_token: str
    real_ip: str


@dataclass(frozen=True, slots=True)
class TelegramConfig:
    enabled: bool
    bot_token: str
    chat_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UrlsConfig:
    apple_developer_rss: str


@dataclass(frozen=True, slots=True)
class WebConfig:
    enabled: bool
    host: str
    port: int


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    enabled: bool
    cron_expr: str
    run_on_startup: bool


@dataclass(frozen=True, slots=True)
class AppConfig:
    weibo: WeiboConfig
    telegram: TelegramConfig
    urls: UrlsConfig
    web: WebConfig
    scheduler: SchedulerConfig


_app_config_cache: AppConfig | None = None


def _load_raw_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise ConfigError(f"Config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a mapping/object")
    return raw


def _require_section(raw: dict[str, Any], section: str) -> dict[str, Any]:
    value = raw.get(section)
    if value is None:
        raise ConfigError(f"Missing config section: {section}")
    if not isinstance(value, dict):
        raise ConfigError(f"Config section '{section}' must be a mapping/object")
    return value


def _require_bool(section: dict[str, Any], key: str, path: str) -> bool:
    value = section.get(key)
    if not isinstance(value, bool):
        raise ConfigError(f"Config field '{path}' must be a boolean")
    return value


def _require_text(section: dict[str, Any], key: str, path: str, *, allow_empty: bool = False) -> str:
    value = section.get(key)
    if isinstance(value, (str, int, float)):
        text = str(value)
    else:
        raise ConfigError(f"Config field '{path}' must be a string-compatible scalar")
    if not allow_empty and not text.strip():
        raise ConfigError(f"Config field '{path}' must not be empty")
    return text


def _require_int(section: dict[str, Any], key: str, path: str) -> int:
    value = section.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"Config field '{path}' must be an integer")
    return value


def _parse_chat_ids(section: dict[str, Any]) -> tuple[str, ...]:
    raw_chat_ids = section.get("chat_ids")
    if not isinstance(raw_chat_ids, list) or not raw_chat_ids:
        raise ConfigError("Config field 'telegram.chat_ids' must be a non-empty list")

    chat_ids: list[str] = []
    for index, value in enumerate(raw_chat_ids):
        if isinstance(value, (str, int)):
            chat_id = str(value).strip()
        else:
            raise ConfigError(f"Config field 'telegram.chat_ids[{index}]' must be a string-compatible scalar")
        if not chat_id:
            raise ConfigError(f"Config field 'telegram.chat_ids[{index}]' must not be empty")
        if chat_id.strip("-0123456789") != "":
            raise ConfigError(f"Config field 'telegram.chat_ids[{index}]' looks invalid: expected integer-like string")
        chat_ids.append(chat_id)
    return tuple(chat_ids)


def _validate_weibo_config(section: dict[str, Any]) -> WeiboConfig:
    config = WeiboConfig(
        enabled=_require_bool(section, "enabled", "weibo.enabled"),
        app_key=_require_text(section, "app_key", "weibo.app_key"),
        app_secret=_require_text(section, "app_secret", "weibo.app_secret"),
        redirect_uri=_require_text(section, "redirect_uri", "weibo.redirect_uri"),
        access_token=_require_text(section, "access_token", "weibo.access_token"),
        real_ip=_require_text(section, "real_ip", "weibo.real_ip"),
    )
    if config.enabled and not config.access_token:
        raise ConfigError("Config field 'weibo.access_token' must not be empty when weibo.enabled=true")
    return config


def _validate_telegram_config(section: dict[str, Any]) -> TelegramConfig:
    config = TelegramConfig(
        enabled=_require_bool(section, "enabled", "telegram.enabled"),
        bot_token=_require_text(section, "bot_token", "telegram.bot_token"),
        chat_ids=_parse_chat_ids(section),
    )
    if config.enabled and ":" not in config.bot_token:
        raise ConfigError("Config field 'telegram.bot_token' looks invalid: expected Telegram bot token format")
    return config


def _validate_urls_config(section: dict[str, Any]) -> UrlsConfig:
    config = UrlsConfig(
        apple_developer_rss=_require_text(section, "apple_developer_rss", "urls.apple_developer_rss"),
    )
    if not config.apple_developer_rss.startswith(("http://", "https://")):
        raise ConfigError("Config field 'urls.apple_developer_rss' must start with http:// or https://")
    return config


def _validate_web_config(section: dict[str, Any]) -> WebConfig:
    config = WebConfig(
        enabled=_require_bool(section, "enabled", "web.enabled"),
        host=_require_text(section, "host", "web.host"),
        port=_require_int(section, "port", "web.port"),
    )
    if not (1 <= config.port <= 65535):
        raise ConfigError("Config field 'web.port' must be between 1 and 65535")
    return config


def _validate_scheduler_config(section: dict[str, Any]) -> SchedulerConfig:
    config = SchedulerConfig(
        enabled=_require_bool(section, "enabled", "scheduler.enabled"),
        cron_expr=_require_text(section, "cron_expr", "scheduler.cron_expr"),
        run_on_startup=_require_bool(section, "run_on_startup", "scheduler.run_on_startup"),
    )
    if not croniter.is_valid(config.cron_expr):
        raise ConfigError(f"Config field 'scheduler.cron_expr' is not a valid cron expression: {config.cron_expr}")
    return config


def get_app_config() -> AppConfig:
    global _app_config_cache
    if _app_config_cache is None:
        raw = _load_raw_config()
        _app_config_cache = AppConfig(
            weibo=_validate_weibo_config(_require_section(raw, "weibo")),
            telegram=_validate_telegram_config(_require_section(raw, "telegram")),
            urls=_validate_urls_config(_require_section(raw, "urls")),
            web=_validate_web_config(_require_section(raw, "web")),
            scheduler=_validate_scheduler_config(_require_section(raw, "scheduler")),
        )
    return _app_config_cache


def get_weibo_config() -> WeiboConfig:
    return get_app_config().weibo


def get_telegram_config() -> TelegramConfig:
    return get_app_config().telegram


def get_urls_config() -> UrlsConfig:
    return get_app_config().urls


def get_web_config() -> WebConfig:
    return get_app_config().web


def get_scheduler_config() -> SchedulerConfig:
    return get_app_config().scheduler
