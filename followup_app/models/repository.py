"""Persistence layer for the Customer Follow-Up Reminder System.

CustomerRepository is the only class that knows about the on-disk
storage format. Everything else in the app works with Customer
objects and never touches files directly, keeping persistence
concerns separate from business logic (FollowUpManager) and the UI.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import List

from models.customer import Customer


class RepositoryError(Exception):
    """Raised when customer data cannot be loaded from or saved to disk."""


class CustomerRepository:
    """Loads and saves Customer objects as JSON on disk.

    Attributes:
        file_path: Path to the JSON file used for storage.
    """

    def __init__(self, file_path: str = "customers.json") -> None:
        self.file_path = file_path

    def load(self) -> List[Customer]:
        """Load all customers from the JSON file.

        Returns an empty list if the file does not exist yet (e.g. on
        first run of the app). Raises RepositoryError if the file
        exists but is corrupted or unreadable.
        """
        if not os.path.exists(self.file_path):
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as handle:
                raw_records = json.load(handle)
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"Customer data file '{self.file_path}' is corrupted: {exc}") from exc
        except OSError as exc:
            raise RepositoryError(f"Could not read customer data file '{self.file_path}': {exc}") from exc

        try:
            return [Customer.from_dict(record) for record in raw_records]
        except (KeyError, ValueError) as exc:
            raise RepositoryError(f"Customer data file '{self.file_path}' has an unexpected format: {exc}") from exc

    def save(self, customers: List[Customer]) -> None:
        """Save all customers to the JSON file.

        Writes to a temporary file first and then replaces the target
        file, so a crash or interruption mid-write can't leave behind
        a half-written, corrupted data file.
        """
        data = [customer.to_dict() for customer in customers]
        directory = os.path.dirname(os.path.abspath(self.file_path)) or "."

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                delete=False,
                suffix=".tmp",
            ) as temp_file:
                json.dump(data, temp_file, indent=2)
                temp_path = temp_file.name
            os.replace(temp_path, self.file_path)
        except OSError as exc:
            raise RepositoryError(f"Could not save customer data to '{self.file_path}': {exc}") from exc
