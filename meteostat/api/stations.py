"""
Stations Module

Provides the Stations class for working with weather station metadata.
"""

import os
from typing import List, Optional
from io import BytesIO
import sqlite3

import pandas as pd

from requests import Response
from meteostat.api.inventory import Inventory
from meteostat.api.point import Point
from meteostat.core.cache import cache_service
from meteostat.api.config import config
from meteostat.core.logger import logger
from meteostat.core.network import network_service
from meteostat.enumerations import Provider
from meteostat.typing import Station


class Stations:
    """
    Stations Database
    """

    def _fetch_file(self, stream=False) -> Response:
        """
        Download the SQLite database file from the configured URL
        """
        urls = config.stations_db_endpoints

        if not urls:
            raise Exception("No stations database URLs configured")

        response = network_service.get_from_mirrors(urls, stream=stream)

        if response is None:
            raise Exception("Failed to download the database file")

        return response

    def _get_file_path(self) -> str:
        """
        Get the file path for the SQLite database
        """
        filepath = config.stations_db_file
        ttl = config.stations_db_ttl

        if os.path.exists(filepath) and not cache_service.is_stale(filepath, ttl):
            return filepath

        # Download the database file
        response = self._fetch_file(stream=True)

        # Create cache directory if it doesn't exist
        cache_service.create_cache_dir()

        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return filepath

    def _connect_memory(self) -> sqlite3.Connection:
        """
        Create an in-memory SQLite database and load the downloaded database file into it
        """
        # Download the database file
        response = self._fetch_file()

        # Create an in-memory SQLite database
        conn = sqlite3.connect(":memory:")

        # Read the downloaded database file into memory
        content = BytesIO(response.content)

        # Convert bytes to string and write the content to the in-memory database
        conn.deserialize(content.read())

        return conn

    def _connect_fs(self) -> sqlite3.Connection:
        """
        Connect to the SQLite database file on the filesystem
        """
        file = self._get_file_path()

        if not file:
            raise FileNotFoundError("SQLite database file not found")

        conn = sqlite3.connect(file)

        return conn

    def connect(self, in_memory: Optional[bool] = None) -> sqlite3.Connection:
        """
        Connect to the database
        """
        if in_memory is None:
            in_memory = config.stations_db_file is None

        logger.info("Connecting to stations database (in_memory=%s)", in_memory)

        if in_memory:
            return self._connect_memory()

        return self._connect_fs()

    def query(
        self,
        sql: str,
        index_col: Optional[str | list] = None,
        params: Optional[tuple | dict] = None,
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return the result as a DataFrame
        """
        with self.connect() as conn:
            df = pd.read_sql(sql, conn, index_col=index_col, params=params)

        return df

    def meta(self, station: str) -> Station:
        """
        Get meta data for a specific weather station
        """
        meta = self.query(
            """
            SELECT 
                `stations`.*,
                `names`.`name` as `name`
            FROM `stations` 
            LEFT JOIN `names` ON `stations`.`id` = `names`.`station` 
                AND `names`.`language` = 'en'
            WHERE `stations`.`id` LIKE ?
            """,
            index_col="id",
            params=(station,),
        ).to_dict("records")[0]

        identifiers = self.query(
            "SELECT `key`, `value` FROM `identifiers` WHERE `station` LIKE ?",
            params=(station,),
        ).to_dict("records")

        return Station(
            id=station,
            **meta,
            identifiers={
                identifier["key"]: identifier["value"] for identifier in identifiers
            },
        )

    def inventory(
        self, station: str | List[str], providers: Optional[List[Provider]] = None
    ) -> Inventory:
        """
        Get inventory records for a single weather station
        """
        query = "SELECT station, provider, parameter, start, end, completeness FROM `inventory`"
        station_list = station if isinstance(station, list) else [station]

        # Generate the right number of placeholders (?, ?, ?, ...)
        placeholders = ", ".join(["?"] * len(station_list))
        # Add the placeholders to the query
        query += f" WHERE `station`  IN ({placeholders})"
        # Add the stations to the params
        params = tuple(station_list)

        if providers:
            # Generate the right number of placeholders (?, ?, ?, ...)
            placeholders = ", ".join(["?"] * len(providers))
            # Add the placeholders to the query
            query += f" AND provider IN ({placeholders})"
            # Add the providers to the params
            params += tuple(providers)

        df = self.query(
            query, index_col=["station", "provider", "parameter"], params=params
        )

        return Inventory(df)

    def nearby(self, point: Point, radius=50000, limit=100) -> pd.DataFrame:
        """
        Get a list of weather station IDs ordered by distance
        """
        return self.query(
            """
            SELECT
                `id`,
                `names`.`name` as `name`,
                `country`,
                `region`,
                `latitude`,
                `longitude`,
                `elevation`,
                `timezone`,
                ROUND(
                    (
                        6371000 * acos(
                            cos(radians(:lat)) * cos(radians(`latitude`)) * 
                            cos(radians(`longitude`) - radians(:lon)) + 
                            sin(radians(:lat)) * sin(radians(`latitude`))
                        )
                    ),
                    1
                ) AS `distance`
            FROM
                `stations`
                INNER JOIN `names` ON `stations`.`id` = `names`.`station`
                AND `names`.`language` = "en"
            WHERE
                `distance` <= :radius
            ORDER BY
                `distance`
            LIMIT
                :limit
            """,
            index_col="id",
            params={
                "lat": point.latitude,
                "lon": point.longitude,
                "radius": radius,
                "limit": limit,
            },
        )


stations = Stations()
