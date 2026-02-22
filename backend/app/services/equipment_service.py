"""
Equipment service with business logic.

Usage:
    from app.services.equipment_service import equipment_service

    equipment = equipment_service.get_available()
    equipment_service.schedule_maintenance(1, next_date)
"""
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import and_

from app import db
from app.models.equipment import Equipment, Reservation, EquipmentStatus, ReservationStatus
from app.services.base import BaseService


class EquipmentService(BaseService[Equipment]):
    """Service for equipment operations."""

    model = Equipment
    search_fields = ['name', 'description', 'inventory_number']
    default_order = 'name'

    def get_available(self) -> List[Equipment]:
        """Get all available equipment."""
        return self.find_all_by(status=EquipmentStatus.AVAILABLE)

    def get_by_type(self, equipment_type: str) -> List[Equipment]:
        """Get equipment by type."""
        return self.find_all_by(type=equipment_type)

    def get_needs_maintenance(self) -> List[Equipment]:
        """Get equipment that needs maintenance."""
        today = date.today()
        return Equipment.query.filter(
            Equipment.next_maintenance <= today,
            Equipment.status != EquipmentStatus.RETIRED
        ).all()

    def set_maintenance(self, id: int) -> Equipment:
        """Set equipment status to maintenance."""
        return self.update(id, {'status': EquipmentStatus.MAINTENANCE})

    def set_available(self, id: int) -> Equipment:
        """Set equipment status to available."""
        equipment = self.get_or_404(id)
        equipment.status = EquipmentStatus.AVAILABLE
        equipment.last_maintenance = date.today()
        db.session.commit()
        return equipment

    def retire(self, id: int) -> Equipment:
        """Retire equipment (soft delete)."""
        return self.update(id, {'status': EquipmentStatus.RETIRED})

    def schedule_maintenance(self, id: int, next_date: date) -> Equipment:
        """Schedule next maintenance date."""
        return self.update(id, {'next_maintenance': next_date})

    def get_stats(self) -> Dict[str, int]:
        """Get equipment statistics."""
        return {
            'total': self.count(),
            'available': self.count(status=EquipmentStatus.AVAILABLE),
            'reserved': self.count(status=EquipmentStatus.RESERVED),
            'maintenance': self.count(status=EquipmentStatus.MAINTENANCE),
            'retired': self.count(status=EquipmentStatus.RETIRED),
            'needs_maintenance': len(self.get_needs_maintenance())
        }


class ReservationService(BaseService[Reservation]):
    """Service for reservation operations."""

    model = Reservation
    default_order = 'start_date'

    def create(self, data: Dict[str, Any]) -> Reservation:
        """
        Create reservation with conflict checking.

        Raises:
            ValueError: If equipment is not available or dates conflict
        """
        equipment_id = data['equipment_id']
        start_date = data['start_date']
        end_date = data['end_date']

        # Check equipment availability
        equipment = Equipment.query.get_or_404(equipment_id)
        if equipment.status != EquipmentStatus.AVAILABLE:
            raise ValueError(f'Sprzęt "{equipment.name}" nie jest dostępny')

        # Check for date conflicts
        if self.has_conflict(equipment_id, start_date, end_date):
            raise ValueError('Wybrany termin koliduje z inną rezerwacją')

        return super().create(data)

    def has_conflict(
        self,
        equipment_id: int,
        start_date: datetime,
        end_date: datetime,
        exclude_id: Optional[int] = None
    ) -> bool:
        """Check if reservation dates conflict with existing ones."""
        query = Reservation.query.filter(
            Reservation.equipment_id == equipment_id,
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
            Reservation.start_date < end_date,
            Reservation.end_date > start_date
        )

        if exclude_id:
            query = query.filter(Reservation.id != exclude_id)

        return query.count() > 0

    def confirm(self, id: int) -> Reservation:
        """Confirm a pending reservation."""
        reservation = self.get_or_404(id)
        if reservation.status != ReservationStatus.PENDING:
            raise ValueError('Można potwierdzić tylko oczekujące rezerwacje')

        reservation.status = ReservationStatus.CONFIRMED
        reservation.equipment.status = EquipmentStatus.RESERVED
        db.session.commit()
        return reservation

    def cancel(self, id: int) -> Reservation:
        """Cancel a reservation."""
        reservation = self.get_or_404(id)
        reservation.status = ReservationStatus.CANCELLED

        # Check if equipment should be set back to available
        active_reservations = Reservation.query.filter(
            Reservation.equipment_id == reservation.equipment_id,
            Reservation.id != id,
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
        ).count()

        if active_reservations == 0:
            reservation.equipment.status = EquipmentStatus.AVAILABLE

        db.session.commit()
        return reservation

    def complete(self, id: int) -> Reservation:
        """Mark reservation as completed."""
        reservation = self.get_or_404(id)
        reservation.status = ReservationStatus.COMPLETED
        reservation.equipment.status = EquipmentStatus.AVAILABLE
        db.session.commit()
        return reservation

    def get_active(self) -> List[Reservation]:
        """Get all active (confirmed, ongoing) reservations."""
        now = datetime.utcnow()
        return Reservation.query.filter(
            Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.start_date <= now,
            Reservation.end_date >= now
        ).all()

    def get_upcoming(self, days: int = 7) -> List[Reservation]:
        """Get upcoming reservations within specified days."""
        from datetime import timedelta
        now = datetime.utcnow()
        future = now + timedelta(days=days)

        return Reservation.query.filter(
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
            Reservation.start_date.between(now, future)
        ).order_by(Reservation.start_date).all()


# Singleton instances
equipment_service = EquipmentService()
reservation_service = ReservationService()
