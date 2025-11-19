"""Data models for Apple Notes CLI."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Note:
    """Represents an Apple Note."""

    id: int
    title: str
    identifier: str
    folder: str | None = None
    content: str | None = None
    created: float | None = None
    modified: float | None = None

    @property
    def created_date(self) -> datetime | None:
        """Get created date as datetime (Apple's Core Data timestamp)."""
        if self.created is None:
            return None
        # Core Data timestamps are seconds since 2001-01-01
        return datetime(2001, 1, 1) + timedelta(seconds=self.created)

    @property
    def modified_date(self) -> datetime | None:
        """Get modified date as datetime (Apple's Core Data timestamp)."""
        if self.modified is None:
            return None
        return datetime(2001, 1, 1) + timedelta(seconds=self.modified)


@dataclass
class Folder:
    """Represents an Apple Notes folder."""

    id: int
    title: str
    identifier: str


# Import at end to avoid circular import issues
from datetime import timedelta
