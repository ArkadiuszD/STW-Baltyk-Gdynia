"""
Base service class for CRUD operations.

Usage:
    from app.services.base import BaseService
    from app.models import Member
    from app.schemas import MemberSchema

    class MemberService(BaseService[Member]):
        model = Member
        schema = MemberSchema

    # Usage
    service = MemberService()
    members = service.get_all(page=1, per_page=20)
    member = service.get_by_id(1)
    member = service.create({'first_name': 'Jan', 'last_name': 'Kowalski'})
"""
from abc import ABC
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Tuple

from flask import abort
from marshmallow import Schema
from sqlalchemy import or_

from app import db
from app.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class PaginatedResult(Generic[T]):
    """Container for paginated query results."""

    def __init__(self, items: List[T], total: int, page: int, per_page: int):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    def to_dict(self, schema: Schema) -> Dict[str, Any]:
        """Convert to API response format."""
        return {
            'items': schema.dump(self.items, many=True),
            'total': self.total,
            'page': self.page,
            'pages': self.pages,
            'per_page': self.per_page
        }


class BaseService(Generic[T], ABC):
    """
    Abstract base service with common CRUD operations.

    Subclasses must define:
    - model: The SQLAlchemy model class
    - schema: Optional Marshmallow schema for serialization

    Example:
        class MemberService(BaseService[Member]):
            model = Member
            schema = MemberSchema

            def get_active(self) -> List[Member]:
                return self.model.query.filter_by(status=MemberStatus.ACTIVE).all()
    """
    model: Type[T]
    schema: Optional[Type[Schema]] = None

    # Fields that can be searched with ILIKE
    search_fields: List[str] = []

    # Default ordering (field name or tuple of field names)
    default_order: Optional[str] = None

    def get_by_id(self, id: int) -> Optional[T]:
        """Get record by ID."""
        return self.model.query.get(id)

    def get_or_404(self, id: int) -> T:
        """Get record by ID or raise 404."""
        return self.model.query.get_or_404(id)

    def get_all(
        self,
        page: int = 1,
        per_page: int = 50,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> PaginatedResult[T]:
        """
        Get all records with pagination, search and filtering.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search term for ILIKE on search_fields
            filters: Dictionary of field=value filters
            order_by: Field name to order by

        Returns:
            PaginatedResult with items and metadata
        """
        query = self.model.query

        # Apply filters
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    column = getattr(self.model, field)
                    # Handle enum values
                    if hasattr(column.type, 'enum_class'):
                        try:
                            enum_class = column.type.enum_class
                            value = enum_class(value)
                        except (ValueError, KeyError):
                            continue
                    query = query.filter(column == value)

        # Apply search
        if search and self.search_fields:
            search_term = f'%{search}%'
            conditions = []
            for field_name in self.search_fields:
                if hasattr(self.model, field_name):
                    column = getattr(self.model, field_name)
                    conditions.append(column.ilike(search_term))
            if conditions:
                query = query.filter(or_(*conditions))

        # Apply ordering
        order_field = order_by or self.default_order
        if order_field and hasattr(self.model, order_field):
            query = query.order_by(getattr(self.model, order_field))

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return PaginatedResult(
            items=pagination.items,
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page
        )

    def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record.

        Args:
            data: Dictionary of field values

        Returns:
            Created model instance
        """
        instance = self.model(**data)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, id: int, data: Dict[str, Any]) -> T:
        """
        Update an existing record.

        Args:
            id: Record ID
            data: Dictionary of field values to update

        Returns:
            Updated model instance
        """
        instance = self.get_or_404(id)

        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)

        db.session.commit()
        return instance

    def delete(self, id: int) -> bool:
        """
        Delete a record.

        Args:
            id: Record ID

        Returns:
            True if deleted
        """
        instance = self.get_or_404(id)
        db.session.delete(instance)
        db.session.commit()
        return True

    def exists(self, **kwargs) -> bool:
        """Check if record exists."""
        return self.model.query.filter_by(**kwargs).first() is not None

    def find_by(self, **kwargs) -> Optional[T]:
        """Find first record matching criteria."""
        return self.model.query.filter_by(**kwargs).first()

    def find_all_by(self, **kwargs) -> List[T]:
        """Find all records matching criteria."""
        return self.model.query.filter_by(**kwargs).all()

    def count(self, **kwargs) -> int:
        """Count records, optionally filtered."""
        if kwargs:
            return self.model.query.filter_by(**kwargs).count()
        return self.model.query.count()

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records at once."""
        instances = [self.model(**data) for data in items]
        db.session.add_all(instances)
        db.session.commit()
        return instances


class SoftDeleteMixin:
    """
    Mixin for services that use soft delete instead of hard delete.

    Requires model to have a 'status' field with 'deleted' or similar value.
    """
    deleted_status: Any = None  # Override in subclass

    def soft_delete(self, id: int) -> T:
        """Mark record as deleted without removing from database."""
        if self.deleted_status is None:
            raise NotImplementedError("deleted_status must be set")

        instance = self.get_or_404(id)
        instance.status = self.deleted_status
        db.session.commit()
        return instance
