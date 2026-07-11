"""Dashboard screen: the app's main landing view.

Shows every active customer grouped into Overdue / Due Today /
Upcoming columns (US2), with per-customer actions to mark a
follow-up complete, edit, or delete (US3, US5).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from models.customer import Customer
from services.commands import DeleteCustomerCommand
from services.commands import CommandHistory
from services.manager import FollowUpManager

COLUMN_CONFIG = (
    ("Overdue", "get_overdue", "#f4cccc"),
    ("Due Today", "get_due_today", "#fff2cc"),
    ("Upcoming", "get_upcoming", "#f4f4f4"),
)


class DashboardScreen(tk.Frame):
    """The main dashboard: three columns of customers grouped by urgency."""

    def __init__(
        self,
        parent: tk.Widget,
        manager: FollowUpManager,
        history: CommandHistory,
        on_add_customer: Callable[[], None],
        on_edit_customer: Callable[[Customer], None],
        on_complete_customer: Callable[[Customer], None],
    ) -> None:
        """
        Args:
            parent: The parent Tkinter widget.
            manager: The FollowUpManager providing customer data.
            history: The CommandHistory used to run delete commands.
            on_add_customer: Callback invoked when "+ Add Customer" is clicked.
            on_edit_customer: Callback invoked with a Customer when "Edit" is clicked.
            on_complete_customer: Callback invoked with a Customer when "Complete" is clicked.
        """
        super().__init__(parent)
        self.manager = manager
        self.history = history
        self.on_add_customer = on_add_customer
        self.on_edit_customer = on_edit_customer
        self.on_complete_customer = on_complete_customer

        self._column_frames: dict = {}
        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        toolbar = tk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=(10, 4))
        add_button = tk.Button(toolbar, text="+ Add Customer", command=self.on_add_customer)
        add_button.pack(side="right")

        columns_container = tk.Frame(self)
        columns_container.pack(fill="both", expand=True, padx=10, pady=10)

        for label, _, color in COLUMN_CONFIG:
            column = tk.Frame(columns_container, bg=color, bd=1, relief="solid")
            column.pack(side="left", fill="both", expand=True, padx=5)

            header = tk.Label(column, text=label.upper(), bg=color, font=("TkDefaultFont", 10, "bold"))
            header.pack(pady=(8, 4))

            body = tk.Frame(column, bg=color)
            body.pack(fill="both", expand=True, padx=6, pady=6)

            self._column_frames[label] = body

    def refresh(self) -> None:
        """Re-read customers from the manager and redraw all three columns."""
        for label, getter_name, color in COLUMN_CONFIG:
            body = self._column_frames[label]
            for widget in body.winfo_children():
                widget.destroy()

            customers = getattr(self.manager, getter_name)()
            if not customers:
                empty_label = tk.Label(
                    body,
                    text="No customers here.",
                    bg=color,
                    fg="#666666",
                    font=("TkDefaultFont", 9, "italic"),
                )
                empty_label.pack(pady=20)
                continue

            for customer in customers:
                self._build_customer_card(body, customer, color)

    def _build_customer_card(self, parent: tk.Widget, customer: Customer, bg_color: str) -> None:
        card = tk.Frame(parent, bg="white", bd=1, relief="solid")
        card.pack(fill="x", pady=4)

        name_label = tk.Label(card, text=customer.name, bg="white", font=("TkDefaultFont", 10, "bold"), anchor="w")
        name_label.pack(fill="x", padx=6, pady=(4, 0))

        detail_text = f"{customer.next_followup_date.isoformat()} — {customer.followup_type}"
        detail_label = tk.Label(card, text=detail_text, bg="white", fg="#444444", anchor="w")
        detail_label.pack(fill="x", padx=6)

        actions = tk.Frame(card, bg="white")
        actions.pack(fill="x", padx=6, pady=(2, 4))

        tk.Button(actions, text="Complete", command=lambda c=customer: self.on_complete_customer(c)).pack(
            side="left", padx=(0, 4)
        )
        tk.Button(actions, text="Edit", command=lambda c=customer: self.on_edit_customer(c)).pack(
            side="left", padx=(0, 4)
        )
        tk.Button(actions, text="Delete", command=lambda c=customer: self._handle_delete(c)).pack(side="left")

    def _handle_delete(self, customer: Customer) -> None:
        confirmed = messagebox.askyesno(
            "Confirm delete",
            f"Delete '{customer.name}'? This cannot be undone from the UI.",
        )
        if not confirmed:
            return
        self.history.run(DeleteCustomerCommand(self.manager, customer.id))
        self.refresh()
