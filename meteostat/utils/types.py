"""
Type parsing utilities

This module contains utilities for extracting and validating types
from class annotations without creating circular imports.
"""

from typing import Any, Union


def extract_property_type(cls: type, property_name: str) -> tuple[Any, Any]:
    """
    Extract the expected type for a class property from type annotations.

    Parameters
    ----------
    cls : type
        The class to extract type information from
    property_name : str
        The name of the property to get the type for

    Returns
    -------
    tuple[Any, Any]
        A tuple containing (expected_type, original_type) where:
        - expected_type: The actual type to validate against (unwrapped from Optional)
        - original_type: The original type annotation (including Optional wrapper)

    Raises
    ------
    ValueError
        If the property doesn't exist on the class
    """
    if not hasattr(cls, property_name):
        raise ValueError(f"Property '{property_name}' does not exist")

    # Get type annotations for the class
    annotations = getattr(cls, "__annotations__", {})
    original_type = annotations.get(property_name)

    if original_type is None:
        return None, None

    expected_type = original_type

    # Handle Optional types (extract the inner type)
    if hasattr(original_type, "__origin__") and original_type.__origin__ is Union:
        args = getattr(original_type, "__args__", ())
        if len(args) == 2 and type(None) in args:
            # This is Optional[Type], extract the non-None type
            # Type narrowing: we know len(args) == 2, so both indices are valid
            arg0 = args[0]  # type: ignore
            arg1 = args[1]  # type: ignore
            expected_type = arg0 if arg1 is type(None) else arg1

    return expected_type, original_type


def validate_parsed_value(
    value: Any, expected_type: Any, original_type: Any, property_name: str
) -> Any:
    """
    Validate a parsed value against the expected type and handle special cases.

    Parameters
    ----------
    value : Any
        The parsed value to validate
    expected_type : Any
        The expected type for validation
    original_type : Any
        The original type annotation (for Optional type checking)
    property_name : str
        The name of the property being validated (for error messages)

    Returns
    -------
    Any
        The validated (and potentially converted) value

    Raises
    ------
    ValueError
        If the value doesn't match the expected type
    """
    # Check if the parsed value matches the expected type
    if isinstance(value, expected_type):
        return value

    # Special case for Optional types - None is allowed
    if (
        hasattr(original_type, "__origin__")
        and original_type.__origin__ is Union
        and value is None
    ):
        return value

    # Special case for bool type - allow 0 and 1 to be parsed as False and True
    if expected_type is bool and isinstance(value, int):
        if value == 0:
            return False
        if value == 1:
            return True
        raise ValueError(
            f"Environment variable '{property_name}' has value {value} "
            f"but boolean type only accepts 0, 1, true, or false"
        )

    # Type mismatch
    raise ValueError(
        f"Environment variable '{property_name}' has type {type(value).__name__} "
        f"but expected {expected_type.__name__}"
    )
