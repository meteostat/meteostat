"""
Cache Service

The Cache Service provides utilities for caching data on the local file system.
"""

from functools import wraps
from hashlib import md5
import json
import os
from os.path import exists
from time import time
from typing import Any, Callable, Optional

import pandas as pd

from meteostat.api.config import config
from meteostat.core.logger import logger


class CacheService:
    """
    Cache Service
    """

    _purged = False  # Flag to indicate if cache has been purged automatically

    @staticmethod
    def _write_pickle(path: str, df: Optional[pd.DataFrame]) -> None:
        """
        Persist a DataFrame in Pickle format
        """
        if df is None:
            pd.DataFrame().to_pickle(path)
        else:
            df.to_pickle(path)

    @staticmethod
    def _read_pickle(path) -> Optional[pd.DataFrame]:
        """
        Read a pickle file into a DataFrame
        """
        df: pd.DataFrame = pd.read_pickle(path)
        return None if df.empty else df

    @staticmethod
    def _write_json(path: str, data: dict | list) -> None:
        """
        Persist data in JSON format
        """
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file)

    @staticmethod
    def _read_json(path) -> dict | list:
        """
        Read JSON data into memory
        """
        with open(path, "r", encoding="utf-8") as file:
            raw = file.read()
        return json.loads(raw)

    @staticmethod
    def _func_to_uid(func, args: tuple, kwargs: dict[str, Any]) -> str:
        """
        Get a unique ID from a function call based on its module, name and arguments
        """
        return md5(
            ";".join(
                (
                    func.__module__,
                    func.__name__,
                    *map(str, args),
                    *[f"{key}:{str(value)}" for key, value in kwargs.items()],
                )
            ).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def create_cache_dir() -> None:
        """
        Create the cache directory if it doesn't exist
        """
        cache_dir = config.cache_directory

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    @staticmethod
    def get_cache_path(uid: str, filetype: str):
        """
        Get path of a cached file based on its uid and file type
        """
        return config.cache_directory + os.sep + f"{uid}.{filetype}"

    @staticmethod
    def is_stale(path: str, ttl: int) -> bool:
        """
        Check if a cached file is stale based on its age and TTL
        """
        return time() - os.path.getmtime(path) > max([ttl, config.cache_ttl])

    @staticmethod
    def purge(ttl: Optional[int] = None) -> None:
        """
        Remove stale files from disk cache
        """
        if ttl is None:
            ttl = config.cache_ttl

        logger.debug("Removing cached files older than %s seconds", ttl)

        cache_dir = config.cache_directory

        if os.path.exists(cache_dir):
            # Get current time
            now = time()
            # Go through all files
            for file in os.listdir(cache_dir):
                # Get full path
                path = os.path.join(cache_dir, file)
                # Check if file is older than TTL
                if now - os.path.getmtime(path) > ttl and os.path.isfile(path):
                    # Delete file
                    os.remove(path)

    def persist(
        self, path: str, data: pd.DataFrame | dict | list, data_type: str
    ) -> None:
        """
        Persist any given data under a specific path
        """
        # Create cache directory if it doesn't exist
        self.create_cache_dir()
        # Save data locally
        if data_type == "json" and isinstance(data, (dict, list)):
            self._write_json(path, data)
        elif data_type == "pickle" and (isinstance(data, pd.DataFrame) or data is None):
            self._write_pickle(path, data)

    def fetch(self, path, data_type: str) -> pd.DataFrame | dict | list | None:
        """
        Fetch data from a given path
        """
        if data_type == "json":
            return self._read_json(path)
        return self._read_pickle(path)

    def from_func(
        self, func, args, kwargs, ttl: int, data_format: str
    ) -> pd.DataFrame | dict | list:
        """
        Cache a function's return value
        """
        uid = self._func_to_uid(func, args, kwargs)  # Get UID for function call
        path = self.get_cache_path(uid, data_format)  # Get the local cache path
        result = (
            self.fetch(path, data_format)
            if ttl > 0 and exists(path) and not self.is_stale(path, ttl)
            else False
        )

        cache_status = "is" if isinstance(result, pd.DataFrame) or result else "is not"
        logger.debug(
            "%s from module %s with args=%s and kwargs=%s returns %s and %s served from cache",
            func.__name__,
            func.__module__,
            args,
            kwargs,
            data_format,
            cache_status,
        )

        if isinstance(result, pd.DataFrame) or result:
            return result

        result = func(*args, **kwargs)
        if ttl > 0:
            self.persist(path, result, data_format)

        return result

    def cache(
        self,
        ttl: int | Callable[..., int] = 60 * 60 * 24,
        data_format: str = "json",
    ):
        """
        A simple decorator which caches a function's return value
        based on its payload.

        All data is persisted in either JSON or Pickle format.
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not config.cache_enable:
                    logger.debug(
                        "Omitting cache for %s from module %s with args=%s and kwargs=%s",
                        func.__name__,
                        func.__module__,
                        args,
                        kwargs,
                    )
                    return func(*args, **kwargs)
                if config.cache_autoclean and not self._purged:
                    self.purge()
                    self._purged = True
                return self.from_func(
                    func,
                    args,
                    kwargs,
                    ttl if isinstance(ttl, int) else ttl(*args, **kwargs),
                    data_format,
                )

            return wrapper

        return decorator


cache_service = CacheService()
purge = cache_service.purge
