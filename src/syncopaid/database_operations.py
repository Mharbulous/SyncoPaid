"""
Database CRUD operations for activity events.

Provides:
- Insert single or batch events
- Query events with filtering
- Delete events by date range or IDs

This module consolidates all database operation mixins.
"""

from .database_operations_events import EventOperationsMixin
from .database_operations_transitions import TransitionOperationsMixin
from .database_operations_clients import ClientOperationsMixin
from .database_operations_matters import MatterOperationsMixin


class OperationsMixin(
    EventOperationsMixin,
    TransitionOperationsMixin,
    ClientOperationsMixin,
    MatterOperationsMixin
):
    """
    Consolidated mixin providing all database CRUD operations.

    Requires _get_connection() method from ConnectionMixin.

    Combines:
    - EventOperationsMixin: Event CRUD operations
    - TransitionOperationsMixin: Transition tracking
    - ClientOperationsMixin: Client management
    - MatterOperationsMixin: Matter management
    """
    pass
