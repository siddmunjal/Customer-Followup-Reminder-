"""Domain models for the Customer Follow-Up Reminder System.

This module defines the two core data classes used throughout the
application: Customer (a lead/contact a sales rep is tracking) and
FollowUpRecord (a single logged interaction with that customer).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

VALID_FOLLOWUP_TYPES = ("Call", "Email", "Meeting", "Other")


@dataclass
class FollowUpRecord:
    """A single completed follow-up interaction with a customer.

    Attributes:
        record_date: The date the interaction took place.
        followup_type: One of VALID_FOLLOWUP_TYPES.
        note: Free-text note describing what happened.
    """

    record_date: date
    followup_type: str
    note: str

    def __post_init__(self) -> None:
        if self.followup_type not in VALID_FOLLOWUP_TYPES:
            raise ValueError(f"followup_type must be one of {VALID_FOLLOWUP_TYPES}, " f"got {self.followup_type!r}")


@dataclass
class Customer:
    """A customer/lead being tracked for follow-up.

    Attributes:
        name: The customer's display name.
        contact_info: Phone number or email address.
        next_followup_date: The date the rep should next reach out.
        followup_type: Planned type of the next follow-up.
        notes: Free-text notes about the customer.
        active: False once a customer is archived (no further contact).
        history: Chronological list of past FollowUpRecord entries.
        id: Unique identifier, generated automatically.
    """

    name: str
    contact_info: str
    next_followup_date: date
    followup_type: str = "Call"
    notes: str = ""
    active: bool = True
    history: List[FollowUpRecord] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        self._validate_name(self.name)
        self._validate_contact_info(self.contact_info)
        if self.followup_type not in VALID_FOLLOWUP_TYPES:
            raise ValueError(f"followup_type must be one of {VALID_FOLLOWUP_TYPES}, " f"got {self.followup_type!r}")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Customer name cannot be empty.")

    @staticmethod
    def _validate_contact_info(contact_info: str) -> None:
        if not contact_info or not contact_info.strip():
            raise ValueError("Customer contact info cannot be empty.")

    def is_overdue(self, today: Optional[date] = None) -> bool:
        """True if the next follow-up date has already passed."""
        today = today or date.today()
        return self.active and self.next_followup_date < today

    def is_due_today(self, today: Optional[date] = None) -> bool:
        """True if the next follow-up is due today."""
        today = today or date.today()
        return self.active and self.next_followup_date == today

    def is_upcoming(self, today: Optional[date] = None) -> bool:
        """True if the next follow-up is scheduled for a future date."""
        today = today or date.today()
        return self.active and self.next_followup_date > today

    def schedule_followup(self, next_date: date, followup_type: str = "Call") -> None:
        """Set (or reset) the next follow-up date and type.

        Raises:
            ValueError: If next_date is in the past, or followup_type
                is not a recognized type.
        """
        if next_date < date.today():
            raise ValueError("Next follow-up date must not be in the past.")
        if followup_type not in VALID_FOLLOWUP_TYPES:
            raise ValueError(f"followup_type must be one of {VALID_FOLLOWUP_TYPES}, " f"got {followup_type!r}")
        self.next_followup_date = next_date
        self.followup_type = followup_type

    def mark_complete(
        self,
        note: str,
        completed_type: Optional[str] = None,
        record_date: Optional[date] = None,
    ) -> FollowUpRecord:
        """Log the current follow-up as complete and add it to history.

        Does NOT schedule the next follow-up automatically -- call
        schedule_followup() (or archive()) afterward, matching the
        two distinct user actions (US3 then US4) in the requirements.

        Returns:
            The FollowUpRecord that was created and appended to history.
        """
        record = FollowUpRecord(
            record_date=record_date or date.today(),
            followup_type=completed_type or self.followup_type,
            note=note,
        )
        self.history.append(record)
        return record

    def archive(self) -> None:
        """Mark this customer as no longer needing follow-up (US4-AC2)."""
        self.active = False

    def to_dict(self) -> dict:
        """Serialize this customer to a plain dict (for JSON persistence)."""
        return {
            "id": self.id,
            "name": self.name,
            "contact_info": self.contact_info,
            "next_followup_date": self.next_followup_date.isoformat(),
            "followup_type": self.followup_type,
            "notes": self.notes,
            "active": self.active,
            "history": [
                {
                    "record_date": r.record_date.isoformat(),
                    "followup_type": r.followup_type,
                    "note": r.note,
                }
                for r in self.history
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        """Rebuild a Customer (with history) from a dict produced by to_dict()."""
        customer = cls(
            name=data["name"],
            contact_info=data["contact_info"],
            next_followup_date=date.fromisoformat(data["next_followup_date"]),
            followup_type=data.get("followup_type", "Call"),
            notes=data.get("notes", ""),
            active=data.get("active", True),
            id=data["id"],
        )
        customer.history = [
            FollowUpRecord(
                record_date=date.fromisoformat(r["record_date"]),
                followup_type=r["followup_type"],
                note=r["note"],
            )
            for r in data.get("history", [])
        ]
        return customer
