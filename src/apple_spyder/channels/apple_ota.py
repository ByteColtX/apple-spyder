from __future__ import annotations

import plistlib
import urllib.request
from dataclasses import dataclass


@dataclass(slots=True)
class AccessoryFirmwarePayload:
    release_date: str
    firmware_version: str
    firmware_build: str
    firmware_download_size_mb: float


class AppleOtaChannel:
    def fetch_accessory_firmware(self, ota_update_url: str) -> AccessoryFirmwarePayload:
        with urllib.request.urlopen(ota_update_url) as response:
            firmware_release_date = response.headers["last-modified"]
            plist_content = plistlib.loads(response.read())

        asset = plist_content["Assets"][0]
        firmware_version = f"{asset['FirmwareVersionMajor']}.{asset['FirmwareVersionMinor']}.{asset['FirmwareVersionRelease']}"
        firmware_build = asset["Build"]
        firmware_download_size_mb = asset["_DownloadSize"] / 1024 / 1024

        return AccessoryFirmwarePayload(
            release_date=firmware_release_date,
            firmware_version=firmware_version,
            firmware_build=firmware_build,
            firmware_download_size_mb=firmware_download_size_mb,
        )
