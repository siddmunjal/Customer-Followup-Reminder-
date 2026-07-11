"""Business logic layer for the Customer Follow-Up Reminder System.

FollowUpManager is the single source of truth for the in-memory list
of customers during a running session. It coordinates with
CustomerRepository for persistence and exposes the grouping queries
(overdue / due today / upcoming) that the Dashboard screen displays.
Nothing outside this class should read or write customers.json
directly, and nothing outside this class should hold its own copy of
the customer list.
"""

from __future__ import annotations

from typing import List, Optional

from models.customer import Customer
from models.repository import CustomerRepository

# Fields a caller is allowed to change via edit_customer(). Deliberately
# excludes id, active, and history -- those are managed through their
# own dedicated methods (archive(), mark_complete()) rather than a
# generic attribute update, so those state transitions stay explicit.
EDITABLE_FIELDS = frozenset({"name", "contact_info", "notes", "next_followup_date", "followup_type"})


class FollowUpManager:
    """Owns the customer list for the running session and persists changes.

    Attributes:
        repository: The CustomerRepository used to load/save customers.
        customers: The in-memory list of Customer objects.
    """

    def __init__(self, repository: CustomerRepository) -> None:
        self.repository = repository
        self.customers: List[Customer] = repository.load()

    def add_customer(self, customer: Customer) -> None:
        """Add a new customer and persist the updated list."""
        self.customers.append(customer)
        self._save()

    def edit_customer(self, customer_id: str, **changes) -> Customer:
        """Update one or more editable fields on an existing customer.

        Args:
            customer_id: The id of the customer to update.
            **changes: Field name/value pairs to set. Keys must be in
                EDITABLE_FIELDS.

        Raises:
            ValueError: If no customer with customer_id exists.
            AttributeError: If a key in changes is not an editable field.
        """
        customer = self._require_customer(customer_id)
        for field_name, value in changes.items():
            if field_name not in EDITABLE_FIELDS:
                raise AttributeError(f"'{field_name}' is not editable. Editable fields are: {sorted(EDITABLE_FIELDS)}")
            setattr(customer, field_name, value)
        self._save()
        return customer

    def delete_customer(self, customer_id: str) -> Customer:
        """Remove a customer permanently and persist the updated list.

        Raises:
            ValueError: If no customer with customer_id exists.
        """
        customer = self._require_customer(customer_id)
        self.customers.remove(customer)
        self._save()
        return customer

    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        """Return the customer with the given id, or None if not found."""
        return next((c for c in self.customers if c.id == customer_id), None)

    def get_overdue(self) -> List[Customer]:
        """Active customers whose next follow-up date has passed, oldest first."""
        overdue = [c for c in self.customers if c.is_overdue()]
        return sorted(overdue, key=lambda c: c.next_followup_date)

    def get_due_today(self) -> List[Customer]:
        """Active customers whose next follow-up is today."""
        return [c for c in self.customers if c.is_due_today()]

    def get_upcoming(self) -> List[Customer]:
        """Active customers with a future next follow-up date, soonest first."""
        upcoming = [c for c in self.customers if c.is_upcoming()]
        return sorted(upcoming, key=lambda c: c.next_followup_date)

    def _require_customer(self, customer_id: str) -> Customer:
        customer = self.find_by_id(customer_id)
        if customer is None:
            raise ValueError(f"No customer found with id '{customer_id}'.")
        return customer

    def save(self) -> None:
        """Persist the current in-memory customer list to disk.

        Public entry point for callers (e.g. commands) that mutate a
        Customer object directly via its own methods -- such as
        mark_complete() or archive() -- rather than going through
        add_customer()/edit_customer()/delete_customer(), and
        therefore need to trigger persistence themselves.
        """
        self._save()

    def _save(self) -> None:
        self.repository.save(self.customers)
