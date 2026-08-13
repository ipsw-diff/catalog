from __future__ import annotations


def appledb_platform(catalog_platform: str, device: str) -> str:
    if catalog_platform == "iOS" and device.startswith("iPad"):
        return "iPadOS"
    return catalog_platform
