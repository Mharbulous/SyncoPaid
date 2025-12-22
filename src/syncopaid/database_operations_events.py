"""
Database CRUD operations for activity events.

Provides:
- Insert single or batch events
- Query events with filtering
- Delete events by date range or IDs
"""

from .database_operations_events_conversion import EventConversionMixin
from .database_operations_events_insert import EventInsertMixin
from .database_operations_events_query import EventQueryMixin
from .database_operations_events_update import EventUpdateMixin
from .database_operations_events_delete import EventDeleteMixin


class EventOperationsMixin(
    EventConversionMixin,
    EventInsertMixin,
    EventQueryMixin,
    EventUpdateMixin,
    EventDeleteMixin
):
    """
    Mixin providing event-related database CRUD operations.

    Requires _get_connection() method from ConnectionMixin.

    Combines functionality from:
    - EventConversionMixin: Row-to-dictionary conversion
    - EventInsertMixin: Insert operations
    - EventQueryMixin: Query operations
    - EventUpdateMixin: Update operations
    - EventDeleteMixin: Delete operations
    """
    pass
