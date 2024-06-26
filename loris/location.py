# -*- coding: utf-8 -*-
"""
loris.core.location
~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

from typing import Optional

import pytz as tz
from loris import LocalResourceException, LocalResourceUnavailableException


class LocationException(LocalResourceException):
    """
    Raise if an error occurred accessing the location.

    """


class LocationUnavailableException(LocalResourceUnavailableException, LocationException):
    """
    Raise if a configured location access can not be found.

    """


class Location:
    """
    Location objects are convenient containers for latitude, longitude,
    timezone, and altitude data associated with a particular
    geographic location.

    Parameters
    ----------
    latitude : float.
        Positive is north of the equator.
        Use decimal degrees notation.
    longitude : float.
        Positive is east of the prime meridian.
        Use decimal degrees notation.
    timezone : str or pytz.timezone, default is 'UTC'.
        See
        http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        for a list of valid time zones.
    altitude : float, default 0.
        Altitude from sea level in meters.
    """

    SECTION = "location"

    def __init__(
        self,
        latitude: float,
        longitude: float,
        timezone: str | tz.BaseTzInfo = tz.UTC,
        altitude: Optional[float] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        if isinstance(timezone, str):
            self._timezone = tz.timezone(timezone)
        elif isinstance(timezone, tz.BaseTzInfo):
            self._timezone = timezone
        elif isinstance(timezone, (int, float)):
            self._timezone = tz.FixedOffset(timezone * 60)
        else:
            raise TypeError("Invalid tz specification")

        self._altitude = altitude

        # TODO: deduct country, state and timezone from latitude and longitude
        #       with geopy and save to override config file
        self.country = country
        self.state = state

    def __repr__(self):
        attrs = ["latitude", "longitude", "altitude", "timezone"]
        return f"\t{Location.SECTION}: \n" + "\t\n".join(f"{attr}: {str(getattr(self, attr))}" for attr in attrs)

    @property
    def timezone(self) -> tz.BaseTzInfo:
        return self._timezone

    @property
    def altitude(self) -> float:
        if self._altitude is None:
            return 0.0
        return self._altitude
