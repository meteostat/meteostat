"""
Guard functions for Meteostat.

The code is licensed under the MIT license.
"""

from datetime import datetime
from meteostat.api.config import config
from meteostat.core.logger import logger
from meteostat.enumerations import Granularity
from meteostat.typing import Request


def request_size_guard(req: Request) -> None:
    """
    Guard to block large requests
    """
    if not config.block_large_requests:
        logger.debug("Large request blocking is disabled.")
        return

    if isinstance(req.station, list) and len(req.station) > 10:
        raise ValueError(
            "Requests with more than 10 stations are blocked by default. "
            "To enable large requests, set `config.block_large_requests = False`."
        )

    if req.granularity not in [Granularity.HOURLY, Granularity.DAILY]:
        return

    if req.start is None:
        raise ValueError(
            "Hourly and daily requests without a start date are blocked by default. "
            "To enable large requests, set `config.block_large_requests = False`."
        )

    time_diff_years = abs((req.end or datetime.now()).year - req.start.year)

    logger.debug(f"Request time range: {time_diff_years} years.")

    if req.granularity is Granularity.HOURLY and time_diff_years > 3:
        raise ValueError(
            "Hourly requests longer than 3 years are blocked by default. "
            "To enable large requests, set `config.block_large_requests = False`."
        )

    if req.granularity is Granularity.DAILY and time_diff_years > 30:
        raise ValueError(
            "Daily requests longer than 30 years are blocked by default. "
            "To enable large requests, set `config.block_large_requests = False`."
        )
