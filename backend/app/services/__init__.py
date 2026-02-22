"""
Services module - business logic layer.

Usage:
    from app.services import member_service, equipment_service

    members = member_service.get_active()
    equipment = equipment_service.get_available()
"""
from app.services.base import BaseService, PaginatedResult, SoftDeleteMixin
from app.services.member_service import MemberService, member_service
from app.services.equipment_service import (
    EquipmentService,
    ReservationService,
    equipment_service,
    reservation_service
)

__all__ = [
    # Base classes
    'BaseService',
    'PaginatedResult',
    'SoftDeleteMixin',
    # Services
    'MemberService',
    'member_service',
    'EquipmentService',
    'equipment_service',
    'ReservationService',
    'reservation_service',
]
