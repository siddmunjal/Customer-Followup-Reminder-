"""Add/Edit customer screen, and the Complete Follow-up dialog.

AddEditScreen implements US1 (add a customer) and part of US5 (edit a
customer) -- the same form is reused for both, pre-filled when
editing. CompleteFollowUpDialog implements US3 (log a completed
follow-up) and US4 (schedule the next one, or archive).
"""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk
from typing import Callable, Optional

from models.customer import VALID_FOLLOWUP_TYPES, Customer
from services.commands import AddCustomerCommand, CompleteFollowUpCommand, EditCustomerCommand, CommandHistory
from services.manager import FollowUpManager


def _parse_date(text: str) -> date:
    """Parse a YYYY-MM-DD string into a date, raising ValueError with a clear message."""
    text = text.strip()
    if not text:
        raise ValueError("Date is required.")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("Enter a valid date in YYYY-MM-DD format.") from exc


class AddEditScreen(tk.Toplevel):
    """Modal form for adding a new customer or editing an existing one (US1, US5)."""

    def __init__(
        self,
        parent: tk.Widget,
        manager: FollowUpManager,
        history: CommandHistory,
        on_saved: Callable[[], None],
        customer: Optional[Customer] = None,
    ) -> None:
        """
        Args:
            parent: The parent Tkinter widget.
            manager: The FollowUpManager to add/edit the customer through.
            history: The CommandHistory used to run add/edit commands.
            on_saved: Callback invoked after a successful save (e.g. to refresh the dashboard).
            customer: If provided, the screen edits this customer; otherwise it adds a new one.
        """
        super().__init__(parent)
        self.manager = manager
        self.history = history
        self.on_saved = on_saved
        self.customer = customer

        self.title("Edit Customer" if customer else "Add Customer")
        self.resizable(False, False)
        self.transient(parent)

        self._build_form()
        if customer is not None:
            self._prefill(customer)

        self.grab_set()

    def _build_form(self) -> None:
        padding = {"padx": 10, "pady": 6}

        tk.Label(self, text="Name *").grid(row=0, column=0, sticky="w", **padding)
        self.name_entry = tk.Entry(self, width=32)
        self.name_entry.grid(row=0, column=1, **padding)

        tk.Label(self, text="Phone / Email *").grid(row=1, column=0, sticky="w", **padding)
        self.contact_entry = tk.Entry(self, width=32)
        self.contact_entry.grid(row=1, column=1, **padding)

        tk.Label(self, text="Follow-up Type").grid(row=2, column=0, sticky="w", **padding)
        self.followup_type_var = tk.StringVar(value=VALID_FOLLOWUP_TYPES[0])
        followup_type_menu = ttk.Combobox(
            self, textvariable=self.followup_type_var, values=VALID_FOLLOWUP_TYPES, state="readonly", width=29
        )
        followup_type_menu.grid(row=2, column=1, **padding)

        tk.Label(self, text="Next Follow-up Date *").grid(row=3, column=0, sticky="w", **padding)
        self.date_entry = tk.Entry(self, width=32)
        self.date_entry.insert(0, (date.today() + timedelta(days=1)).isoformat())
        self.date_entry.grid(row=3, column=1, **padding)

        tk.Label(self, text="Notes").grid(row=4, column=0, sticky="nw", **padding)
        self.notes_text = tk.Text(self, width=32, height=4)
        self.notes_text.grid(row=4, column=1, **padding)

        self.error_label = tk.Label(self, text="", fg="#a33333")
        self.error_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=10)

        button_row = tk.Frame(self)
        button_row.grid(row=6, column=0, columnspan=2, pady=(6, 10))
        tk.Button(button_row, text="Cancel", command=self.destroy).pack(side="left", padx=6)
        tk.Button(button_row, text="Save", command=self._handle_save).pack(side="left", padx=6)

    def _prefill(self, customer: Customer) -> None:
        self.name_entry.insert(0, customer.name)
        self.contact_entry.insert(0, customer.contact_info)
        self.followup_type_var.set(customer.followup_type)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, customer.next_followup_date.isoformat())
        self.notes_text.insert("1.0", customer.notes)

    def _handle_save(self) -> None:
        self.error_label.config(text="")
        try:
            name = self.name_entry.get().strip()
            if not name:
                raise ValueError("Name is required.")

            contact_info = self.contact_entry.get().strip()
            if not contact_info:
                raise ValueError("Phone or email is required.")

            next_date = _parse_date(self.date_entry.get())
            if next_date < date.today():
                raise ValueError("Next follow-up date must not be in the past.")

            followup_type = self.followup_type_var.get()
            notes = self.notes_text.get("1.0", tk.END).strip()

            if self.customer is None:
                new_customer = Customer(
                    name=name,
                    contact_info=contact_info,
                    next_followup_date=next_date,
                    followup_type=followup_type,
                    notes=notes,
                )
                self.history.run(AddCustomerCommand(self.manager, new_customer))
            else:
                self.history.run(
                    EditCustomerCommand(
                        self.manager,
                        self.customer.id,
                        name=name,
                        contact_info=contact_info,
                        next_followup_date=next_date,
                        followup_type=followup_type,
                        notes=notes,
                    )
                )
        except ValueError as exc:
            self.error_label.config(text=str(exc))
            return

        self.on_saved()
        self.destroy()


class CompleteFollowUpDialog(tk.Toplevel):
    """Modal dialog to log a completed follow-up and schedule the next one (US3, US4)."""

    def __init__(
        self,
        parent: tk.Widget,
        manager: FollowUpManager,
        history: CommandHistory,
        customer: Customer,
        on_saved: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.manager = manager
        self.history = history
        self.customer = customer
        self.on_saved = on_saved

        self.title(f"Complete Follow-up — {customer.name}")
        self.resizable(False, False)
        self.transient(parent)

        self._build_form()
        self.grab_set()

    def _build_form(self) -> None:
        padding = {"padx": 10, "pady": 6}

        tk.Label(self, text="What happened? *").grid(row=0, column=0, sticky="nw", **padding)
        self.note_text = tk.Text(self, width=32, height=4)
        self.note_text.grid(row=0, column=1, **padding)

        self.schedule_next_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self,
            text="Schedule another follow-up",
            variable=self.schedule_next_var,
            command=self._toggle_next_fields,
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=10)

        tk.Label(self, text="Next Follow-up Date").grid(row=2, column=0, sticky="w", **padding)
        self.next_date_entry = tk.Entry(self, width=32)
        self.next_date_entry.insert(0, (date.today() + timedelta(days=7)).isoformat())
        self.next_date_entry.grid(row=2, column=1, **padding)

        tk.Label(self, text="Next Follow-up Type").grid(row=3, column=0, sticky="w", **padding)
        self.next_type_var = tk.StringVar(value=self.customer.followup_type)
        ttk.Combobox(
            self, textvariable=self.next_type_var, values=VALID_FOLLOWUP_TYPES, state="readonly", width=29
        ).grid(row=3, column=1, **padding)

        self.error_label = tk.Label(self, text="", fg="#a33333")
        self.error_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10)

        button_row = tk.Frame(self)
        button_row.grid(row=5, column=0, columnspan=2, pady=(6, 10))
        tk.Button(button_row, text="Cancel", command=self.destroy).pack(side="left", padx=6)
        tk.Button(button_row, text="Save", command=self._handle_save).pack(side="left", padx=6)

    def _toggle_next_fields(self) -> None:
        state = "normal" if self.schedule_next_var.get() else "disabled"
        self.next_date_entry.config(state=state)

    def _handle_save(self) -> None:
        self.error_label.config(text="")
        try:
            note = self.note_text.get("1.0", tk.END).strip()
            if not note:
                raise ValueError("Please describe what happened.")

            next_date = None
            if self.schedule_next_var.get():
                next_date = _parse_date(self.next_date_entry.get())

            command = CompleteFollowUpCommand(
                self.manager,
                self.customer.id,
                note=note,
                next_followup_date=next_date,
                next_followup_type=self.next_type_var.get(),
            )
            self.history.run(command)
        except ValueError as exc:
            self.error_label.config(text=str(exc))
            return

        self.on_saved()
        self.destroy()
