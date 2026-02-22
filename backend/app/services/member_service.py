"""
Member service with business logic.

Usage:
    from app.services.member_service import MemberService

    service = MemberService()
    members = service.get_all(page=1, search='Kowalski')
    member = service.create({'first_name': 'Jan', ...})
"""
from datetime import datetime
from typing import Dict, Any, List, Optional

from app import db
from app.models import Member
from app.models.member import MemberStatus
from app.models.fee import Fee, FeeStatus
from app.services.base import BaseService, SoftDeleteMixin


class MemberService(SoftDeleteMixin, BaseService[Member]):
    """Service for member operations."""

    model = Member
    search_fields = ['first_name', 'last_name', 'email', 'member_number']
    default_order = 'last_name'
    deleted_status = MemberStatus.FORMER

    def create(self, data: Dict[str, Any]) -> Member:
        """
        Create a new member with consent handling.

        Args:
            data: Member data dictionary

        Returns:
            Created member

        Raises:
            ValueError: If email already exists
        """
        # Check for duplicates
        if self.exists(email=data['email']):
            raise ValueError('Email już istnieje w systemie')

        if data.get('member_number') and self.exists(member_number=data['member_number']):
            raise ValueError('Numer członkowski już istnieje')

        # Handle status conversion
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = MemberStatus(data['status'])

        # Handle RODO consent
        if data.get('data_consent'):
            data['consent_date'] = datetime.utcnow()

        return super().create(data)

    def update(self, id: int, data: Dict[str, Any]) -> Member:
        """
        Update member with duplicate checking.

        Args:
            id: Member ID
            data: Fields to update

        Returns:
            Updated member

        Raises:
            ValueError: If email/member_number duplicate
        """
        member = self.get_or_404(id)

        # Check email uniqueness
        if 'email' in data and data['email'] != member.email:
            if self.exists(email=data['email']):
                raise ValueError('Email już istnieje w systemie')

        # Check member_number uniqueness
        if 'member_number' in data and data['member_number'] != member.member_number:
            if self.exists(member_number=data['member_number']):
                raise ValueError('Numer członkowski już istnieje')

        # Handle status conversion
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = MemberStatus(data['status'])

        # Handle RODO consent
        if 'data_consent' in data:
            if data['data_consent'] and not member.data_consent:
                data['consent_date'] = datetime.utcnow()

        return super().update(id, data)

    def get_active(self) -> List[Member]:
        """Get all active members."""
        return self.find_all_by(status=MemberStatus.ACTIVE)

    def get_with_debt(self) -> List[Member]:
        """Get members with unpaid fees."""
        return Member.query.join(Fee).filter(
            Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE])
        ).distinct().all()

    def get_stats(self) -> Dict[str, int]:
        """Get member statistics."""
        total = self.count()
        active = self.count(status=MemberStatus.ACTIVE)
        suspended = self.count(status=MemberStatus.SUSPENDED)
        former = self.count(status=MemberStatus.FORMER)

        # Members with debt
        members_with_debt = db.session.query(Fee.member_id).filter(
            Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE])
        ).distinct().count()

        return {
            'total': total,
            'active': active,
            'suspended': suspended,
            'former': former,
            'with_debt': members_with_debt
        }

    def deactivate(self, id: int) -> Member:
        """
        Deactivate member (soft delete).

        Sets status to FORMER.
        """
        return self.soft_delete(id)


# Singleton instance for convenience
member_service = MemberService()
