"""
Test types module

The code is licensed under the MIT license.
"""

import types

import pytest

from meteostat.utils.types import extract_property_type, validate_parsed_value


class SampleClass:
    """Sample class for testing type extraction"""

    # Use default values to make hasattr work correctly
    name: str = "default"
    age: int = 0
    optional_value: str | None = None
    score: float = 0.0
    tags: list[str] = []
    settings: dict[str, str] = {}
    optional_tags: list[str] | None = None


class TestExtractPropertyType:
    """Test extract_property_type function"""

    def test_extract_property_type_string(self):
        """Test extracting string type annotation"""
        expected_type, original_type = extract_property_type(SampleClass, "name")
        assert expected_type is str
        assert original_type is str

    def test_extract_property_type_int(self):
        """Test extracting int type annotation"""
        expected_type, original_type = extract_property_type(SampleClass, "age")
        assert expected_type is int
        assert original_type is int

    def test_extract_property_type_float(self):
        """Test extracting float type annotation"""
        expected_type, original_type = extract_property_type(SampleClass, "score")
        assert expected_type is float
        assert original_type is float

    def test_extract_property_type_optional(self):
        """Test extracting Optional type annotation"""
        expected_type, original_type = extract_property_type(
            SampleClass, "optional_value"
        )
        # For str | None, expected_type should be str
        assert expected_type is str
        # original_type should be a union type (str | None creates types.UnionType)
        assert isinstance(original_type, types.UnionType)
        assert str in original_type.__args__
        assert type(None) in original_type.__args__

    def test_extract_property_type_nonexistent(self):
        """Test extracting type for nonexistent property"""
        with pytest.raises(ValueError) as excinfo:
            extract_property_type(SampleClass, "nonexistent")
        assert "does not exist" in str(excinfo.value)

    def test_extract_property_type_with_no_annotations(self):
        """Test extracting type from class with property not in annotations"""

        # Create an instance and try to get a property that doesn't have annotations
        class MinimalClass:
            pass

        with pytest.raises(ValueError) as excinfo:
            extract_property_type(MinimalClass, "any_prop")
        assert "does not exist" in str(excinfo.value)

    def test_extract_property_type_list(self):
        """Test extracting List type annotation"""
        expected_type, original_type = extract_property_type(SampleClass, "tags")
        # For list[str], expected_type should be list[str]
        assert hasattr(expected_type, "__origin__")
        assert expected_type.__origin__ is list

    def test_extract_property_type_dict(self):
        """Test extracting Dict type annotation"""
        expected_type, original_type = extract_property_type(SampleClass, "settings")
        # For dict[str, str], expected_type should be dict[str, str]
        assert hasattr(expected_type, "__origin__")
        assert expected_type.__origin__ is dict

    def test_extract_property_type_optional_list(self):
        """Test extracting list[str] | None type annotation"""
        expected_type, original_type = extract_property_type(
            SampleClass, "optional_tags"
        )
        # For list[str] | None, expected_type should be list[str]
        assert hasattr(expected_type, "__origin__")
        assert expected_type.__origin__ is list
        # original_type should be a union type (list[str] | None creates types.UnionType)
        assert isinstance(original_type, types.UnionType)
        assert type(None) in original_type.__args__


class TestValidateParsedValue:
    """Test validate_parsed_value function"""

    def test_validate_parsed_value_matching_type(self):
        """Test validation when value matches expected type"""
        value = "test string"
        expected_type = str
        original_type = str
        result = validate_parsed_value(value, expected_type, original_type, "name")
        assert result == value

    def test_validate_parsed_value_int_matching(self):
        """Test validation with matching int type"""
        value = 42
        expected_type = int
        original_type = int
        result = validate_parsed_value(value, expected_type, original_type, "age")
        assert result == value

    def test_validate_parsed_value_float_matching(self):
        """Test validation with matching float type"""
        value = 3.14
        expected_type = float
        original_type = float
        result = validate_parsed_value(value, expected_type, original_type, "score")
        assert result == value

    def test_validate_parsed_value_bool_from_zero(self):
        """Test validation converting int 0 to bool False"""
        value = 0
        expected_type = bool
        original_type = bool
        result = validate_parsed_value(value, expected_type, original_type, "is_active")
        assert result is False

    def test_validate_parsed_value_bool_from_one(self):
        """Test validation converting int 1 to bool True"""
        value = 1
        expected_type = bool
        original_type = bool
        result = validate_parsed_value(value, expected_type, original_type, "is_active")
        assert result is True

    def test_validate_parsed_value_bool_from_invalid_int(self):
        """Test validation fails for invalid int to bool conversion"""
        value = 2
        expected_type = bool
        original_type = bool
        with pytest.raises(ValueError) as excinfo:
            validate_parsed_value(value, expected_type, original_type, "is_active")
        assert "boolean type only accepts" in str(excinfo.value)

    def test_validate_parsed_value_optional_with_none(self):
        """Test validation of None value for Optional type"""
        original_type = str | None
        value = None
        expected_type = str
        result = validate_parsed_value(
            value, expected_type, original_type, "optional_field"
        )
        assert result is None

    def test_validate_parsed_value_type_mismatch(self):
        """Test validation fails for type mismatch"""
        value = "string value"
        expected_type = int
        original_type = int
        with pytest.raises(ValueError) as excinfo:
            validate_parsed_value(value, expected_type, original_type, "age")
        assert "has type" in str(excinfo.value)
        assert "but expected" in str(excinfo.value)

    def test_validate_parsed_value_optional_with_matching_value(self):
        """Test validation of matching value for Optional type"""
        original_type = str | None
        value = "valid string"
        expected_type = str
        result = validate_parsed_value(
            value, expected_type, original_type, "optional_field"
        )
        assert result == value

    def test_validate_parsed_value_list_type(self):
        """Test validation with list type"""
        value = [1, 2, 3]
        expected_type = list
        original_type = list
        result = validate_parsed_value(value, expected_type, original_type, "items")
        assert result == value

    def test_validate_parsed_value_dict_type(self):
        """Test validation with dict type"""
        value = {"key": "value"}
        expected_type = dict
        original_type = dict
        result = validate_parsed_value(value, expected_type, original_type, "mapping")
        assert result == value

    def test_validate_parsed_value_list_parameterized(self):
        """Test validation with parameterized list[str] type"""
        value = ["item1", "item2", "item3"]
        expected_type = list[str]
        original_type = list[str]
        result = validate_parsed_value(value, expected_type, original_type, "tags")
        assert result == value

    def test_validate_parsed_value_dict_parameterized(self):
        """Test validation with parameterized dict[str, str] type"""
        value = {"key1": "value1", "key2": "value2"}
        expected_type = dict[str, str]
        original_type = dict[str, str]
        result = validate_parsed_value(value, expected_type, original_type, "settings")
        assert result == value

    def test_validate_parsed_value_optional_list_with_value(self):
        """Test validation with list[str] | None and valid list value"""
        value = ["item1", "item2"]
        expected_type = list[str]
        original_type = list[str] | None
        result = validate_parsed_value(
            value, expected_type, original_type, "optional_tags"
        )
        assert result == value

    def test_validate_parsed_value_optional_list_with_none(self):
        """Test validation with list[str] | None and None value"""
        value = None
        expected_type = list[str]
        original_type = list[str] | None
        result = validate_parsed_value(
            value, expected_type, original_type, "optional_tags"
        )
        assert result is None

    def test_validate_parsed_value_list_type_mismatch(self):
        """Test validation fails for type mismatch with list[str]"""
        value = "not a list"
        expected_type = list[str]
        original_type = list[str]
        with pytest.raises(ValueError) as excinfo:
            validate_parsed_value(value, expected_type, original_type, "tags")
        assert "has type" in str(excinfo.value)
        assert "but expected" in str(excinfo.value)

    def test_validate_parsed_value_dict_type_mismatch(self):
        """Test validation fails for type mismatch with dict[str, str]"""
        value = ["not", "a", "dict"]
        expected_type = dict[str, str]
        original_type = dict[str, str]
        with pytest.raises(ValueError) as excinfo:
            validate_parsed_value(value, expected_type, original_type, "settings")
        assert "has type" in str(excinfo.value)
        assert "but expected" in str(excinfo.value)


class TestTypeExtractionIntegration:
    """Integration tests for type extraction and validation"""

    def test_extract_and_validate_string_property(self):
        """Test extracting and validating string property"""
        expected_type, original_type = extract_property_type(SampleClass, "name")
        value = "John Doe"
        result = validate_parsed_value(value, expected_type, original_type, "name")
        assert result == "John Doe"

    def test_extract_and_validate_int_property(self):
        """Test extracting and validating int property"""
        expected_type, original_type = extract_property_type(SampleClass, "age")
        value = 30
        result = validate_parsed_value(value, expected_type, original_type, "age")
        assert result == 30

    def test_validate_string_type(self):
        """Test simple string validation"""
        expected_type = str
        original_type = str
        value = "test"
        result = validate_parsed_value(value, expected_type, original_type, "test_prop")
        assert result == "test"

    def test_validate_int_type(self):
        """Test simple int validation"""
        expected_type = int
        original_type = int
        value = 42
        result = validate_parsed_value(value, expected_type, original_type, "test_prop")
        assert result == 42
