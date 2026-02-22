"""
Base model classes and mixins for SQLAlchemy models.

Usage:
    from app.models.base import BaseModel, TimestampMixin

    class MyModel(BaseModel):
        __tablename__ = 'my_models'
        name = db.Column(db.String(100))

    # Or with just timestamps:
    class AnotherModel(TimestampMixin, db.Model):
        __tablename__ = 'another_models'
        id = db.Column(db.Integer, primary_key=True)
"""
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar

from app import db

T = TypeVar('T', bound='BaseModel')


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns."""

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class BaseModel(TimestampMixin, db.Model):
    """
    Abstract base model with common fields and methods.

    Provides:
    - id: Primary key
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - to_dict(): Convert to dictionary
    - save(): Commit changes
    - delete(): Remove from database
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    def to_dict(self, include: Optional[list] = None, exclude: Optional[list] = None) -> Dict[str, Any]:
        """
        Convert model to dictionary.

        Args:
            include: List of fields to include (if None, include all)
            exclude: List of fields to exclude

        Returns:
            Dictionary representation of the model
        """
        exclude = exclude or []
        result = {}

        for column in self.__table__.columns:
            if column.name in exclude:
                continue
            if include and column.name not in include:
                continue

            value = getattr(self, column.name)

            # Handle special types
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, 'value'):  # Enum
                value = value.value

            result[column.name] = value

        return result

    def save(self) -> 'BaseModel':
        """Save the model to database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> None:
        """Delete the model from database."""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs) -> 'BaseModel':
        """
        Update model attributes.

        Args:
            **kwargs: Attributes to update

        Returns:
            Updated model instance
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    @classmethod
    def get_by_id(cls: Type[T], id: int) -> Optional[T]:
        """Get model by ID or None if not found."""
        return cls.query.get(id)

    @classmethod
    def get_or_404(cls: Type[T], id: int) -> T:
        """Get model by ID or raise 404."""
        return cls.query.get_or_404(id)

    @classmethod
    def get_all(cls: Type[T]) -> list[T]:
        """Get all records."""
        return cls.query.all()

    @classmethod
    def count(cls: Type[T]) -> int:
        """Count all records."""
        return cls.query.count()

    @classmethod
    def exists(cls: Type[T], **kwargs) -> bool:
        """Check if record with given attributes exists."""
        return cls.query.filter_by(**kwargs).first() is not None

    @classmethod
    def find_by(cls: Type[T], **kwargs) -> Optional[T]:
        """Find first record matching criteria."""
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def find_all_by(cls: Type[T], **kwargs) -> list[T]:
        """Find all records matching criteria."""
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def create(cls: Type[T], **kwargs) -> T:
        """Create and save a new record."""
        instance = cls(**kwargs)
        return instance.save()

    def __repr__(self):
        """Default string representation."""
        return f'<{self.__class__.__name__} id={self.id}>'
