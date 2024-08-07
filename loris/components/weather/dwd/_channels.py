# -*- coding: utf-8 -*-
"""
loris.connector.weather.dwd._channels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from typing import Any, Collection, Dict

from loris.components.weather import Weather
from loris.components.weather.constants import WEATHER as CHANNEL_NAMES

CHANNEL_IDS = [
    Weather.GHI,
    Weather.TEMP_AIR,
    Weather.TEMP_DEW_POINT,
    Weather.PRESSURE_SEA,
    Weather.WIND_SPEED,
    Weather.WIND_SPEED_GUST,
    Weather.WIND_DIRECTION,
    Weather.CLOUD_COVER,
    Weather.SUNSHINE,
    Weather.VISIBILITY,
    Weather.PRECIPITATION,
    Weather.PRECIPITATION_PROB,
    "condition",
    "icon",
]

CHANNEL_ADDRESS_ALIAS = {
    Weather.GHI:                 "solar",
    Weather.TEMP_AIR:            "temperature",
    Weather.PRESSURE_SEA:        "pressure_msl",
    Weather.WIND_SPEED_GUST:     "wind_gust_speed",
    Weather.WIND_DIRECTION_GUST: "wind_gust_direction",
}

CHANNEL_TYPE_DEFAULT = float
CHANNEL_TYPES = {
    Weather.SUNSHINE: int,
    Weather.VISIBILITY: int,
    Weather.PRECIPITATION_PROB: int,
    "condition": str,
    "icon": str,
}


def _parse_name(channel_id: str) -> str:
    return channel_id.replace("_", " ").title() if channel_id not in CHANNEL_NAMES else CHANNEL_NAMES[channel_id]


def _parse_address(channel_id: str) -> str:
    return channel_id if channel_id not in CHANNEL_ADDRESS_ALIAS else CHANNEL_ADDRESS_ALIAS[channel_id]


def _parse_type(channel_id: str) -> type:
    return CHANNEL_TYPE_DEFAULT if channel_id not in CHANNEL_TYPES else CHANNEL_TYPES[channel_id]


def _parse_channel(channel_id: str, **channel: Any) -> Dict[str, Any]:
    channel["id"] = channel_id
    channel["name"] = _parse_name(channel_id)
    channel["address"] = _parse_address(channel_id)
    channel["type"] = _parse_type(channel_id)
    if channel["type"] == str:  # noqa: E721
        channel["length"] = 32
    return channel


def get_channels(**channel: Any) -> Collection[Dict[str, Any]]:
    channels = []
    for channel_id in CHANNEL_IDS:
        channels.append(_parse_channel(channel_id, **channel))
    return channels
