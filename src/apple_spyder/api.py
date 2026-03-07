from __future__ import annotations

import logging
from datetime import datetime
from http import HTTPStatus
from typing import Any

import flask
from werkzeug.exceptions import HTTPException

from apple_spyder.channels.apple_rss import AppleDeveloperRssChannel
from apple_spyder.channels.notifier import Notifier
from apple_spyder.logging_config import configure_logging
from apple_spyder.services import accessory_updates, software_releases
from apple_spyder.settings import ROOT_DIR

configure_logging()
logger = logging.getLogger("api")

app = flask.Flask(__name__, template_folder=str(ROOT_DIR / "templates"))
app.config["DEBUG"] = False


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = HTTPStatus.BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def json_response(*, data: dict[str, Any] | list[Any] | None = None, message: str = "ok", status_code: int = HTTPStatus.OK) -> flask.Response:
    return flask.jsonify(
        {
            "ok": 200 <= int(status_code) < 300,
            "message": message,
            "data": data,
        }
    ), int(status_code)


@app.errorhandler(ApiError)
def handle_api_error(error: ApiError) -> tuple[flask.Response, int]:
    return json_response(message=error.message, status_code=error.status_code)


@app.errorhandler(HTTPException)
def handle_http_error(error: HTTPException) -> tuple[flask.Response, int]:
    return json_response(message=error.description, status_code=error.code or HTTPStatus.INTERNAL_SERVER_ERROR)


@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception) -> tuple[flask.Response, int]:
    logger.exception("Unhandled API error")
    return json_response(message=str(error), status_code=HTTPStatus.INTERNAL_SERVER_ERROR)


@app.route("/", methods=["GET"])
def api_welcome() -> str:
    return flask.render_template("index.html")


@app.route("/apple-spyder/software-release", methods=["GET"])
def api_check_software_release() -> tuple[flask.Response, int]:
    result = software_releases.main()
    return json_response(message="software release check completed", data=result)


@app.route("/apple-spyder/software-release/feed", methods=["GET"])
def api_view_software_release_feed() -> tuple[flask.Response, int]:
    feed = AppleDeveloperRssChannel().fetch_feed()
    entries = list(getattr(feed, "entries", []) or [])
    feed_title = getattr(feed.feed, "title", "Apple Developer Releases")
    first_entry_published = getattr(entries[0], "published", None) if entries else None
    feed_updated = getattr(feed.feed, "updated", None) or first_entry_published

    data = {
        "feed": {
            "title": feed_title,
            "updated_at": feed_updated,
            "entry_count": len(entries),
        },
        "entries": [
            {
                "title": getattr(entry, "title", None),
                "link": getattr(entry, "link", None),
                "published": getattr(entry, "published", None),
                "summary": getattr(entry, "summary", None),
            }
            for entry in entries
        ],
    }
    return json_response(message="software release feed fetched", data=data)


@app.route("/apple-spyder/accessory-ota-update", methods=["GET"])
def api_check_accessory_ota_update() -> tuple[flask.Response, int]:
    result = accessory_updates.main()
    return json_response(message="accessory ota update check completed", data=result)


@app.route("/apple-spyder/test-notify", methods=["GET", "POST"])
def api_test_notify() -> tuple[flask.Response, int]:
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    message = flask.request.values.get("message") or f"apple-spyder test notification at {now}"
    Notifier().send_message(message)
    return json_response(
        message="test notification sent",
        data={
            "sent": True,
            "message": message,
        },
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5005)
