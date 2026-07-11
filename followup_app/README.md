# Customer Follow-Up Reminder System

A desktop application for sales reps to track customer follow-ups so no lead or
active deal falls through the cracks. Reps log a customer along with a next
contact date; the app surfaces who's overdue, due today, or coming up soon,
and keeps a history of every past interaction.

## Why this exists

Sales reps handling more than a handful of leads at once tend to lose track
of follow-ups when relying on memory, sticky notes, or ad-hoc spreadsheets.
A missed follow-up can mean a lost deal or a customer who feels forgotten.
This tool replaces that manual tracking with a simple, always-up-to-date
dashboard.

## Features

- Add, edit, and delete customers with contact info and a next follow-up date
- Dashboard grouping customers into **Overdue**, **Due Today**, and **Upcoming**
- Mark a follow-up complete, log a note, and schedule the next one (or archive
  the customer if no further contact is needed)
- Full history of past follow-ups kept per customer
- All actions run through a Command pattern, giving the app a built-in,
  undoable audit trail of everything a rep has done

## Requirements

- Python 3.10+
- `tkinter` (ships with most Python installs; on Ubuntu/Debian, install with
  `sudo apt install python3-tk` if you get a `ModuleNotFoundError`)

No other dependencies are required — everything else is Python's standard
library.

## Installation

```bash
git clone <this-repository-url>
cd followup_app
```

That's it — there's no build step and no external packages to install.

## Running the application

```bash
python3 main.py
```

This opens the Dashboard, the app's main screen. Customer data is saved
automatically to `customers.json` in the same folder, so your data will
still be there the next time you launch the app.

## Using the application

**Dashboard (main screen)**
- Customers are grouped into three columns: **Overdue**, **Due Today**, and
  **Upcoming**, based on each customer's next follow-up date.
- Each customer card has three actions:
  - **Complete** — log what happened on this follow-up, then either schedule
    the next one or mark the customer as no longer needing contact.
  - **Edit** — update the customer's name, contact info, notes, follow-up
    type, or next follow-up date.
  - **Delete** — permanently remove the customer (asks for confirmation
    first).
- Click **+ Add Customer** at the top to add a new customer.

**Add / Edit Customer**
- Name and Phone/Email are required.
- The next follow-up date must be entered as `YYYY-MM-DD` and must be a
  future date — the form will show an inline error if it's missing, badly
  formatted, or in the past.

**Complete Follow-up**
- Describing what happened is required.
- Uncheck "Schedule another follow-up" if there's no further contact needed;
  the customer will be archived and will no longer appear on the dashboard.

## Project structure

```
followup_app/
├── models/
│   ├── customer.py       # Customer and FollowUpRecord data classes
│   └── repository.py     # JSON persistence (CustomerRepository)
├── services/
│   ├── manager.py         # Business logic: grouping, add/edit/delete
│   └── commands.py        # Command pattern (add/edit/delete/complete + undo)
├── gui/
│   ├── dashboard.py        # Main dashboard screen
│   └── add_edit.py         # Add/Edit form and Complete Follow-up dialog
├── main.py                  # Application entry point
└── flake8-report/           # Generated lint report (see below)
```

## Code quality

This project follows PEP 8, enforced with a `flake8` configuration
(`max-line-length = 119`) and formatted with `black` and `isort`. A full
lint report is available at `flake8-report/index.html`.
