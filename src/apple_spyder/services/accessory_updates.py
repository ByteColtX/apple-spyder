from __future__ import annotations

import logging
from typing import Any

from apple_spyder.channels.apple_ota import AppleOtaChannel
from apple_spyder.channels.notifier import Notifier
from apple_spyder.repositories.accessory_update_repository import AccessoryUpdateRepository
from apple_spyder.utils.time_utils import convert_to_local_timezone, is_a_previous_time

_DEFAULT_LAST_UPDATE_TIME = "Thu, 01 Jan 1970 00:00:00 UTC"
_AIRPODS_PRO_2_MODEL = "A2618"
_AIRPODS_PRO_2_NAME = "AirPods Pro 2"
_AIRPODS_PRO_2_OTA_URL = (
    "https://mesu.apple.com/assets/com_apple_MobileAsset_UARP_A2618/"
    "com_apple_MobileAsset_UARP_A2618.xml"
)


logger = logging.getLogger("accessory_updates")

def _build_message(last_update_time: str, firmware_release_date: str, firmware_version: str, firmware_build: str, firmware_download_size_mb: float) -> str:
    if is_a_previous_time(last_update_time, firmware_release_date):
        return (
            f"📤 Apple 为 *{_AIRPODS_PRO_2_NAME}* 发布新固件\n\n"
            f"🌀 编译版本：*{firmware_build}*\n"
            f"🔢 版本号：*{firmware_version}*\n"
            f"📦 固件大小：*{firmware_download_size_mb:.2f}* MB\n"
            f"🕐 发布时间: *{convert_to_local_timezone(firmware_release_date).strftime('%Y/%m/%d %H:%M:%S')}*"
        )
    return f"🙊Apple *撤回* {_AIRPODS_PRO_2_NAME} 固件更新至 *{firmware_version}({firmware_build})*"


def main() -> dict[str, Any]:
    ota_channel = AppleOtaChannel()
    notifier = Notifier()
    repository = AccessoryUpdateRepository()

    try:
        payload = ota_channel.fetch_accessory_firmware(_AIRPODS_PRO_2_OTA_URL)
        last_update_time = repository.get_last_update_time(_AIRPODS_PRO_2_MODEL)
        if not last_update_time:
            last_update_time = _DEFAULT_LAST_UPDATE_TIME
            logger.warning("last_update_time is empty in database, set timestamp to: %s", last_update_time)

        has_update = last_update_time != payload.release_date
        if not has_update:
            return {
                "product_name": _AIRPODS_PRO_2_NAME,
                "product_model": _AIRPODS_PRO_2_MODEL,
                "has_update": False,
                "last_update_time": last_update_time,
                "release_date": payload.release_date,
                "firmware_version": payload.firmware_version,
                "firmware_build": payload.firmware_build,
                "firmware_download_size_mb": payload.firmware_download_size_mb,
                "notification_sent": False,
            }

        message = _build_message(
            last_update_time,
            payload.release_date,
            payload.firmware_version,
            payload.firmware_build,
            payload.firmware_download_size_mb,
        )
        logger.info(message)
        notifier.send_message(message, parse_in_markdown=True, weibo_message=message.replace("*", ""))
        repository.update_last_update_time(_AIRPODS_PRO_2_MODEL, payload.release_date)
        logger.info("Update feed publish time in database: %s", payload.release_date)

        return {
            "product_name": _AIRPODS_PRO_2_NAME,
            "product_model": _AIRPODS_PRO_2_MODEL,
            "has_update": True,
            "last_update_time": last_update_time,
            "release_date": payload.release_date,
            "firmware_version": payload.firmware_version,
            "firmware_build": payload.firmware_build,
            "firmware_download_size_mb": payload.firmware_download_size_mb,
            "notification_sent": True,
        }
    finally:
        repository.close()
