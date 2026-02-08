"""
Test config module

The code is licensed under the MIT license.
"""

import os
from typing import List, Optional

import pytest

from meteostat.api.config import ConfigService


class TestConfigService:
    """Test ConfigService class"""

    def test_parse_env_value_string(self):
        """Test parsing string environment variable"""

        class TestConfig(ConfigService):
            mystr: str = "default"

        config = TestConfig(prefix="TEST")
        result = config._parse_env_value("mystr", "test_value")
        assert result == "test_value"

    def test_parse_env_value_int(self):
        """Test parsing int environment variable"""

        class TestConfig(ConfigService):
            myint: int = 0

        config = TestConfig(prefix="TEST")
        result = config._parse_env_value("myint", "42")
        assert result == 42

    def test_parse_env_value_bool(self):
        """Test parsing bool environment variable"""

        class TestConfig(ConfigService):
            mybool: bool = False

        config = TestConfig(prefix="TEST")
        result = config._parse_env_value("mybool", "true")
        assert result is True

    def test_parse_env_value_list_str(self):
        """Test parsing List[str] environment variable"""

        class TestConfig(ConfigService):
            mylist: List[str] = []

        config = TestConfig(prefix="TEST")
        result = config._parse_env_value("mylist", '["item1", "item2", "item3"]')
        assert result == ["item1", "item2", "item3"]

    def test_parse_env_value_optional_list_str(self):
        """Test parsing Optional[List[str]] environment variable"""

        class TestConfig(ConfigService):
            optional_list: Optional[List[str]] = None

        config = TestConfig(prefix="TEST")
        result = config._parse_env_value("optional_list", '["item1", "item2"]')
        assert result == ["item1", "item2"]

    def test_parse_env_value_optional_list_str_with_null(self):
        """Test parsing Optional[List[str]] with null value"""

        class TestConfig(ConfigService):
            optional_list: Optional[List[str]] = None

        config = TestConfig(prefix="TEST")
        result = config._parse_env_value("optional_list", "null")
        assert result is None

    def test_parse_env_value_invalid_json(self):
        """Test that invalid JSON is handled gracefully"""

        class TestConfig(ConfigService):
            mylist: List[str] = []

        config = TestConfig(prefix="TEST")
        result = config._parse_env_value("mylist", "not valid json")
        # Should return the sentinel value, not None
        assert result is config._SKIP_VALUE

    def test_parse_env_value_type_mismatch(self):
        """Test that type mismatch is handled gracefully"""

        class TestConfig(ConfigService):
            mylist: List[str] = []

        config = TestConfig(prefix="TEST")
        # Passing a string instead of a list
        result = config._parse_env_value("mylist", '"not a list"')
        # Should return the sentinel value, not None
        assert result is config._SKIP_VALUE

    def test_load_env_with_valid_list_str(self, monkeypatch):
        """Test loading environment variables with valid List[str]"""

        class TestConfig(ConfigService):
            endpoints: List[str] = ["default1", "default2"]

        monkeypatch.setenv("TEST_ENDPOINTS", '["endpoint1", "endpoint2"]')
        config = TestConfig(prefix="TEST")
        assert config.endpoints == ["endpoint1", "endpoint2"]

    def test_load_env_with_invalid_list_str(self, monkeypatch):
        """Test loading environment variables with invalid List[str] keeps default"""

        class TestConfig(ConfigService):
            endpoints: List[str] = ["default1", "default2"]

        monkeypatch.setenv("TEST_ENDPOINTS", "not a list")
        config = TestConfig(prefix="TEST")
        # Should keep the default value when parsing fails
        assert config.endpoints == ["default1", "default2"]

    def test_load_env_with_optional_list_str(self, monkeypatch):
        """Test loading environment variables with Optional[List[str]]"""

        class TestConfig(ConfigService):
            modes: Optional[List[str]] = None

        monkeypatch.setenv("TEST_MODES", '["mode1", "mode2"]')
        config = TestConfig(prefix="TEST")
        assert config.modes == ["mode1", "mode2"]

    def test_load_env_with_optional_list_str_null(self, monkeypatch):
        """Test loading environment variables with Optional[List[str]] set to null"""

        class TestConfig(ConfigService):
            modes: Optional[List[str]] = ["default"]

        monkeypatch.setenv("TEST_MODES", "null")
        config = TestConfig(prefix="TEST")
        assert config.modes is None

    def test_initialization_does_not_abort_on_invalid_env(self, monkeypatch):
        """Test that initialization continues when environment variable is invalid"""

        class TestConfig(ConfigService):
            mylist: List[str] = ["default"]
            mystring: str = "default_string"

        # Set an invalid list value
        monkeypatch.setenv("TEST_MYLIST", "invalid json")
        # Set a valid string value
        monkeypatch.setenv("TEST_MYSTRING", "valid_string")

        # Initialization should not raise an exception
        config = TestConfig(prefix="TEST")

        # Invalid env var should be ignored, keeping default
        assert config.mylist == ["default"]
        # Valid env var should be loaded
        assert config.mystring == "valid_string"
