"""Command pattern implementation for the Customer Follow-Up Reminder System.

Every user-initiated action (add, edit, delete, complete a follow-up)
is wrapped in a Command object rather than calling FollowUpManager
directly from the GUI. This keeps the GUI layer thin (it only builds
and runs commands) and gives the app a natural, uniform place to log
every action a rep takes -- which doubles as the audit trail behind
the optional Customer Detail/History screen.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from models.customer import Customer
from services.manager import FollowUpManager


class Command(ABC):
    """Base class for a single, executable, (usually) undoable user action."""

    @abstractmethod
    def execute(self) -> None:
        """Perform the action."""

    def undo(self) -> None:
        """Reverse the action performed by execute().

        Subclasses that cannot be meaningfully undone should leave
        this default in place rather than pretending to support it.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support undo.")

    def describe(self) -> str:
        """Human-readable summary of this action, for an audit log/history view."""
        return type(self).__name__


class AddCustomerCommand(Command):
    """Adds a new customer to the system."""

    def __init__(self, manager: FollowUpManager, customer: Customer) -> None:
        self.manager = manager
        self.customer = customer

    def execute(self) -> None:
        self.manager.add_customer(self.customer)

    def undo(self) -> None:
        self.manager.delete_customer(self.customer.id)

    def describe(self) -> str:
        return f"Added customer '{self.customer.name}'"


class EditCustomerCommand(Command):
    """Updates one or more editable fields on an existing customer."""

    def __init__(self, manager: FollowUpManager, customer_id: str, **changes) -> None:
        self.manager = manager
        self.customer_id = customer_id
        self.changes = changes
        self._previous_values: dict = {}

    def execute(self) -> None:
        customer = self.manager.find_by_id(self.customer_id)
        if customer is None:
            raise ValueError(f"No customer found with id '{self.customer_id}'.")
        self._previous_values = {field_name: getattr(customer, field_name) for field_name in self.changes}
        self.manager.edit_customer(self.customer_id, **self.changes)

    def undo(self) -> None:
        self.manager.edit_customer(self.customer_id, **self._previous_values)

    def describe(self) -> str:
        return f"Edited customer '{self.customer_id}': {sorted(self.changes)}"


class DeleteCustomerCommand(Command):
    """Permanently removes a customer from the system."""

    def __init__(self, manager: FollowUpManager, customer_id: str) -> None:
        self.manager = manager
        self.customer_id = customer_id
        self._removed_customer: Optional[Customer] = None

    def execute(self) -> None:
        self._removed_customer = self.manager.delete_customer(self.customer_id)

    def undo(self) -> None:
        if self._removed_customer is None:
            raise RuntimeError("Cannot undo a delete that was never executed.")
        self.manager.add_customer(self._removed_customer)

    def describe(self) -> str:
        name = self._removed_customer.name if self._removed_customer else self.customer_id
        return f"Deleted customer '{name}'"


class CompleteFollowUpCommand(Command):
    """Logs a follow-up as complete, then either schedules the next one or archives.

    This single command covers both US3 (log what happened) and US4
    (schedule the next follow-up, or archive if there's no further
    contact), since in the UI these happen as one "Mark Complete"
    action from the rep's point of view.
    """

    def __init__(
        self,
        manager: FollowUpManager,
        customer_id: str,
        note: str,
        completed_type: Optional[str] = None,
        next_followup_date: Optional[date] = None,
        next_followup_type: str = "Call",
    ) -> None:
        self.manager = manager
        self.customer_id = customer_id
        self.note = note
        self.completed_type = completed_type
        self.next_followup_date = next_followup_date
        self.next_followup_type = next_followup_type

        self._previous_next_date: Optional[date] = None
        self._previous_followup_type: Optional[str] = None
        self._previous_active: Optional[bool] = None

    def execute(self) -> None:
        customer = self.manager.find_by_id(self.customer_id)
        if customer is None:
            raise ValueError(f"No customer found with id '{self.customer_id}'.")

        self._previous_next_date = customer.next_followup_date
        self._previous_followup_type = customer.followup_type
        self._previous_active = customer.active

        customer.mark_complete(self.note, completed_type=self.completed_type)

        if self.next_followup_date is not None:
            customer.schedule_followup(self.next_followup_date, self.next_followup_type)
        else:
            customer.archive()

        self.manager.save()

    def undo(self) -> None:
        customer = self.manager.find_by_id(self.customer_id)
        if customer is None:
            raise RuntimeError(f"Customer '{self.customer_id}' no longer exists; cannot undo.")

        customer.history.pop()
        customer.next_followup_date = self._previous_next_date
        customer.followup_type = self._previous_followup_type
        customer.active = self._previous_active

        self.manager.save()

    def describe(self) -> str:
        return f"Completed follow-up for customer '{self.customer_id}'"


class CommandHistory:
    """Runs commands and keeps a log of executed ones for undo and auditing."""

    def __init__(self) -> None:
        self._executed: list = []

    def run(self, command: Command) -> None:
        """Execute a command and record it in the history."""
        command.execute()
        self._executed.append(command)

    def undo_last(self) -> bool:
        """Undo the most recently executed command, if any.

        Returns:
            True if a command was undone, False if there was nothing to undo.
        """
        if not self._executed:
            return False
        command = self._executed.pop()
        command.undo()
        return True

    @property
    def log(self) -> list:
        """Read-only view of executed commands, oldest first, for an audit trail."""
        return list(self._executed)
