"""
Enum utilities for consistent enum handling across the application.

Provides helper functions for:
- Getting enum values for validation
- Converting strings to enum instances
- Getting display labels for enums
"""
from enum import Enum
from typing import Type, List, Optional, Dict


def enum_values(enum_class: Type[Enum]) -> List[str]:
    """Get list of all enum values (lowercase strings).

    Use in Marshmallow schemas: validate=validate.OneOf(enum_values(MemberStatus))
    """
    return [e.value for e in enum_class]


def enum_names(enum_class: Type[Enum]) -> List[str]:
    """Get list of all enum names (uppercase strings).

    Use when you need the Python enum names, not values.
    """
    return [e.name for e in enum_class]


def to_enum(enum_class: Type[Enum], value: str, default: Optional[Enum] = None) -> Optional[Enum]:
    """Convert string value to enum instance.

    Args:
        enum_class: The enum class to convert to
        value: The string value (case-insensitive)
        default: Default enum to return if value not found

    Returns:
        Enum instance or default if not found
    """
    if value is None:
        return default

    value_lower = value.lower()
    for member in enum_class:
        if member.value.lower() == value_lower or member.name.lower() == value_lower:
            return member
    return default


def enum_choices(enum_class: Type[Enum]) -> List[tuple]:
    """Get list of (value, name) tuples for forms/dropdowns.

    Returns:
        List of tuples: [(value, display_name), ...]
    """
    return [(e.value, e.name.replace('_', ' ').title()) for e in enum_class]


# Re-export all enums for convenient importing
from app.models.member import MemberStatus
from app.models.fee import FeeStatus, FeeFrequency
from app.models.transaction import TransactionType, TransactionCategory
from app.models.equipment import EquipmentType, EquipmentStatus, ReservationStatus
from app.models.event import EventType, EventStatus, ParticipantStatus
from app.models.user import UserRole

__all__ = [
    # Utilities
    'enum_values',
    'enum_names',
    'to_enum',
    'enum_choices',
    # Enums
    'MemberStatus',
    'FeeStatus',
    'FeeFrequency',
    'TransactionType',
    'TransactionCategory',
    'EquipmentType',
    'EquipmentStatus',
    'ReservationStatus',
    'EventType',
    'EventStatus',
    'ParticipantStatus',
    'UserRole',
]
