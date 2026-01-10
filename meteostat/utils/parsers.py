"""
Data parsers

The code is licensed under the MIT license.
"""

import calendar
from typing import List
import datetime

import pandas as pd
import pytz

from meteostat.api.stations import stations as stations_service
from meteostat.api.point import Point
from meteostat.typing import Station


def parse_station(
    station: (str | Station | Point | List[str | Station | Point] | pd.DataFrame),
) -> Station | List[Station]:
    """
    Parse one or multiple station(s) or geo point(s)

    Point objects are converted to virtual stations with IDs like $0001, $0002, etc.
    based on their position in the input list.

    Returns
    -------
    Station | List[Station]
        - Returns a single Station object for single-station input (str, Station, Point)
        - Returns a list of Station objects for multi-station input (list, pd.Index, etc.)
    """
    # Return data if it contains station meta data (single station)
    if isinstance(station, Station):
        return station

    # Handle Point objects (single point)
    if isinstance(station, Point):
        return _point_to_station(station, 1)

    # Handle string (single station ID)
    if isinstance(station, str):
        meta = stations_service.meta(station)
        if meta is None:
            raise ValueError(f'Weather station with ID "{station}" could not be found')
        return meta

    # Convert station identifier(s) to list (multi-station)
    if isinstance(station, pd.DataFrame):
        stations = station.index.tolist()
    else:
        # It's a list
        stations = station

    # Get station meta data
    data = []
    point_counter = 0
    for s in stations:
        # Append data early if it contains station meta data
        if isinstance(s, Station):
            data.append(s)
            continue
        # Handle Point objects
        if isinstance(s, Point):
            point_counter += 1
            data.append(_point_to_station(s, point_counter))
            continue
        # Get station meta data
        meta = stations_service.meta(s)
        # Raise exception if station could not be found
        if meta is None:
            raise ValueError(f'Weather station with ID "{s}" could not be found')
        # Append station meta data
        data.append(meta)

    # Return list of station meta data
    return data


def _point_to_station(point: Point, index: int) -> Station:
    """
    Convert a Point object to a virtual Station object

    Parameters
    ----------
    point : Point
        The Point object to convert
    index : int
        The position in the list of points (1-indexed)

    Returns
    -------
    Station
        A virtual Station object with an ID like $0001
    """
    # Create virtual station ID
    station_id = f"${index:04d}"

    # Create Station object with extracted coordinates
    return Station(
        id=station_id,
        name=f"Location #{index}",
        latitude=point.latitude,
        longitude=point.longitude,
        elevation=point.elevation,
    )


def parse_time(
    value: datetime.date | datetime.datetime | None,
    timezone: str | None = None,
    is_end: bool = False,
) -> datetime.datetime | None:
    """
    Convert a given date/time input to datetime

    To set the time of a date to 23:59:59, pass is_end=True
    """
    if not value:
        return None

    if not isinstance(value, datetime.datetime):
        parsed = datetime.datetime.combine(
            value,
            datetime.datetime.max.time() if is_end else datetime.datetime.min.time(),
        )
    else:
        parsed = value

    if timezone:
        tz = pytz.timezone(timezone)
        # If the datetime is already aware, convert it directly
        # If it's naive, treat it as being in the target timezone
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(pytz.utc).replace(tzinfo=None)
        else:
            parsed = tz.localize(parsed).astimezone(pytz.utc).replace(tzinfo=None)

    return parsed


def parse_month(
    value: datetime.date | datetime.datetime | None, is_end: bool = False
) -> datetime.date | None:
    """
    Convert a given date/time input to the first or last day of the month respectively
    """
    if not value:
        return None

    last_day = calendar.monthrange(value.year, value.month)[1]

    return datetime.date(value.year, value.month, last_day if is_end else 1)


def parse_year(year: int, is_end: bool = False) -> datetime.date:
    """
    Parse a year into a date, returning either the first or last day of the year
    """
    return datetime.date(year, 12, 31) if is_end else datetime.date(year, 1, 1)
