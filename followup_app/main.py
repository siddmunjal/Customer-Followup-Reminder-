"""Entry point for the Customer Follow-Up Reminder System.

Wires together the persistence layer, business logic, command
history, and GUI screens, and starts the Tkinter main loop.
"""

from __future__ import annotations

import tkinter as tk

from gui.add_edit import AddEditScreen, CompleteFollowUpDialog
from gui.dashboard import DashboardScreen
from models.customer import Customer
from models.repository import CustomerRepository
from services.commands import CommandHistory
from services.manager import FollowUpManager

DATA_FILE = "customers.json"


class FollowUpApp:
    """Top-level application: owns the window and coordinates screen navigation."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Customer Follow-Up Reminder")
        self.root.geometry("760x480")

        self.repository = CustomerRepository(DATA_FILE)
        self.manager = FollowUpManager(self.repository)
        self.history = CommandHistory()

        self.dashboard = DashboardScreen(
            self.root,
            self.manager,
            self.history,
            on_add_customer=self._open_add_screen,
            on_edit_customer=self._open_edit_screen,
            on_complete_customer=self._open_complete_dialog,
        )
        self.dashboard.pack(fill="both", expand=True)

    def _open_add_screen(self) -> None:
        AddEditScreen(self.root, self.manager, self.history, on_saved=self.dashboard.refresh)

    def _open_edit_screen(self, customer: Customer) -> None:
        AddEditScreen(self.root, self.manager, self.history, on_saved=self.dashboard.refresh, customer=customer)

    def _open_complete_dialog(self, customer: Customer) -> None:
        CompleteFollowUpDialog(self.root, self.manager, self.history, customer, on_saved=self.dashboard.refresh)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = FollowUpApp()
    app.run()


if __name__ == "__main__":
    main()
