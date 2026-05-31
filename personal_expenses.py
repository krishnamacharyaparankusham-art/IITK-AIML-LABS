"""
personal_expense_tracker.py
============================
Production-ready Personal Expense Tracker
Author  : Krishna Parankusham
Version : 1.0.0

Usage:
    python personal_expense_tracker.py
    python personal_expense_tracker.py --file my_my_expenses.csv
"""

import csv
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# ── Logging configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("expense_tracker.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_FILE = "my_expenses.csv"
CSV_HEADERS   = ["Date", "Category", "Amount", "Description"]
VALID_CATEGORIES = ["Food", "Travel", "Housing", "Health",
                    "Entertainment", "Shopping", "Other"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. ADD EXPENSE
# ─────────────────────────────────────────────────────────────────────────────
def add_expense(expenses: list[dict]) -> None:
    """
    Prompt the user for expense details and append a validated
    record to the expenses list.

    Args:
        expenses: The in-memory list of expense dictionaries.
    """
    print("\n--- Add Expense ---")

    # ── Date ──────────────────────────────────────────────────────────────────
    while True:
        date = input("Enter the date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(date, "%Y-%m-%d")
            break
        except ValueError:
            print("  [Error] Invalid date format. Please use YYYY-MM-DD.")

    # ── Category ──────────────────────────────────────────────────────────────
    print("  Available categories: " +
          ", ".join(f"{i+1}.{c}" for i, c in enumerate(VALID_CATEGORIES)))
    while True:
        cat_input = input("  Enter category (e.g., Food, Travel): ").strip()
        if not cat_input:
            print("  [Error] Category cannot be empty.")
            continue
    
        if cat_input.isdigit():
            num = int(cat_input)
            if 1 <= num <= len(VALID_CATEGORIES):
                category = VALID_CATEGORIES[num - 1]
                break
            else:
                print(f"  [Error] Please enter a number between 1 and {len(VALID_CATEGORIES)}.")
                continue
        else:
            category = cat_input.title()
            break

    # ── Amount ────────────────────────────────────────────────────────────────
    while True:
        try:
            amount = float(input("Enter the amount: ").strip())
            if amount <= 0:
                print("  [Error] Amount must be greater than zero.")
                continue
            break
        except ValueError:
            print("  [Error] Please enter a valid numeric amount.")

    # ── Description ───────────────────────────────────────────────────────────
    while True:
        description = input("Enter a brief description: ").strip()
        if description:
            break
        print("  [Error] Description cannot be empty.")

    record = {
        "date":        date,
        "category":    category,
        "amount":      amount,
        "description": description,
    }
    expenses.append(record)
    logger.info("Expense added: %s", record)
    print("Expense added successfully.")


# ─────────────────────────────────────────────────────────────────────────────
# 2. VIEW EXPENSES
# ─────────────────────────────────────────────────────────────────────────────
def view_expenses(expenses: list[dict]) -> None:
    """
    Display all recorded expenses in a formatted table.
    Skips and reports any incomplete / malformed records.

    Args:
        expenses: The in-memory list of expense dictionaries.
    """
    print("\n--- View Expenses ---")

    if not expenses:
        print("No expenses recorded.")
        return

    required = {"date", "category", "amount", "description"}
    print(f"\n  {'#':<4} {'Date':<12} {'Category':<16} {'Amount':>10}  Description")
    print("  " + "─" * 68)

    valid = 0
    for idx, expense in enumerate(expenses, start=1):
        if not all(key in expense for key in required):
            print(f"  {idx:<4} [Invalid expense record: {expense}]")
            logger.warning("Skipped malformed record at index %d: %s", idx, expense)
            continue
        print(
            f"  {idx:<4} {expense['date']:<12} {expense['category']:<16}"
            f" {expense['amount']:>10.2f}  {expense['description']}"
        )
        valid += 1

    print("  " + "─" * 68)
    total = sum(e["amount"] for e in expenses if "amount" in e)
    print(f"  {'TOTAL':<33} {total:>10.2f}")
    print(f"\n  {valid} valid record(s) displayed.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. SET BUDGET  &  TRACK BUDGET
# ─────────────────────────────────────────────────────────────────────────────
def set_budget() -> float:
    """
    Prompt the user to enter a monthly budget.

    Returns:
        float: The validated monthly budget amount.
    """
    print("\n--- Set Monthly Budget ---")
    while True:
        try:
            budget = float(input("Enter your monthly budget: ").strip())
            if budget <= 0:
                print("  [Error] Budget must be greater than zero.")
                continue
            logger.info("Monthly budget set to %.2f", budget)
            return budget
        except ValueError:
            print("  [Error] Please enter a valid numeric amount.")


def track_budget(expenses: list[dict], budget: float) -> None:
    """
    Calculate total expenses and compare against the monthly budget.
    Warns the user if the budget is exceeded; shows remaining balance otherwise.
    Also displays a per-category spending breakdown.

    Args:
        expenses: The in-memory list of expense dictionaries.
        budget:   The monthly budget set by the user.
    """
    print("\n--- Track Budget ---")

    total_expenses = sum(expense["amount"] for expense in expenses
                         if "amount" in expense)

    print(f"\n  Monthly Budget : {budget:.2f}")
    print(f"  Total Expenses : {total_expenses:.2f}")

    if total_expenses > budget:
        overspend = total_expenses - budget
        print(f"\n  ⚠  WARNING: You have exceeded your budget by {overspend:.2f}!")
        logger.warning("Budget exceeded by %.2f", overspend)
    else:
        remaining = budget - total_expenses
        print(f"\n  ✔  You are within your budget. You have {remaining:.2f} remaining.")

    # Per-category breakdown
    if expenses:
        print("\n  Spending by Category:")
        category_totals: dict[str, float] = {}
        for exp in expenses:
            cat = exp.get("category", "Unknown")
            category_totals[cat] = category_totals.get(cat, 0.0) + exp.get("amount", 0.0)
        for cat, amt in sorted(category_totals.items(), key=lambda x: -x[1]):
            bar = "█" * int(amt / max(category_totals.values()) * 20)
            print(f"    {cat:<16} {amt:>10.2f}  {bar}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. SAVE & LOAD EXPENSES
# ─────────────────────────────────────────────────────────────────────────────
def save_expenses(expenses: list[dict], filename: str = DEFAULT_FILE) -> None:
    """
    Persist all expense records to a CSV file.

    Args:
        expenses: The in-memory list of expense dictionaries.
        filename: Target CSV file path (default: my_expenses.csv).
    """
    try:
        filepath = Path(filename)
        with filepath.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_HEADERS)
            for expense in expenses:
                writer.writerow([
                    expense.get("date",        ""),
                    expense.get("category",    ""),
                    expense.get("amount",      0.0),
                    expense.get("description", ""),
                ])
        logger.info("Saved %d expense(s) to '%s'.", len(expenses), filename)
        print(f"Expenses saved successfully to '{filename}'.")
    except (IOError, OSError) as exc:
        logger.error("Failed to save expenses: %s", exc)
        print(f"  [Error] Could not save file: {exc}")


def load_expenses(filename: str = DEFAULT_FILE) -> list[dict]:
    """
    Load expense records from a CSV file into memory.
    Skips and logs any malformed rows.

    Args:
        filename: Source CSV file path (default: my_expenses.csv).

    Returns:
        list[dict]: List of valid expense dictionaries.
    """
    expenses: list[dict] = []
    filepath = Path(filename)

    if not filepath.exists():
        print("No existing expenses found. Starting fresh.")
        logger.info("No existing file at '%s'. Starting fresh.", filename)
        return expenses

    try:
        with filepath.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if all(key in row for key in CSV_HEADERS):
                    try:
                        expense = {
                            "date":        row["Date"].strip(),
                            "category":    row["Category"].strip(),
                            "amount":      float(row["Amount"]),
                            "description": row["Description"].strip(),
                        }
                        expenses.append(expense)
                    except ValueError:
                        logger.warning("Skipping row with invalid amount: %s", row)
                        print(f"  [Warning] Skipping invalid record: {row}")
                else:
                    logger.warning("Skipping incomplete row: %s", row)
                    print(f"  [Warning] Skipping incomplete row: {row}")
        logger.info("Loaded %d expense(s) from '%s'.", len(expenses), filename)
        print(f"Loaded {len(expenses)} expense(s) from '{filename}'.")
    except (IOError, OSError) as exc:
        logger.error("Failed to load expenses: %s", exc)
        print(f"  [Error] Could not read file: {exc}")

    return expenses


# ─────────────────────────────────────────────────────────────────────────────
# 5. INTERACTIVE MENU
# ─────────────────────────────────────────────────────────────────────────────
def show_menu() -> None:
    """Print the main navigation menu."""
    print("\n" + "=" * 32)
    print("    Personal Expense Tracker")
    print("=" * 32)
    print("  1. Add Expense")
    print("  2. View Expenses")
    print("  3. Track Budget")
    print("  4. Save Expenses")
    print("  5. Exit")
    print("=" * 32)


def main(filename: str = DEFAULT_FILE) -> None:
    """
    Application entry point.
    Loads saved expenses, sets the monthly budget, then enters the
    interactive menu loop.

    Args:
        filename: CSV file used for persistence.
    """
    print("\nWelcome to Personal Expense Tracker!")
    print("-" * 32)

    # Load previous data
    expenses = load_expenses(filename)

    # Set budget upfront (matches sample solution design)
    budget = set_budget()

    menu_actions = {
        "1": lambda: add_expense(expenses),
        "2": lambda: view_expenses(expenses),
        "3": lambda: track_budget(expenses, budget),
        "4": lambda: save_expenses(expenses, filename),
    }

    while True:
        show_menu()
        choice = input("Enter your choice (1-5): ").strip()

        if choice in menu_actions:
            menu_actions[choice]()
        elif choice == "5":
            save_expenses(expenses, filename)
            logger.info("Application exited by user.")
            print("Exiting... Goodbye!")
            break
        else:
            print("  [Error] Invalid choice. Please select a number between 1 and 5.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Personal Expense Tracker – CLI application"
    )
    parser.add_argument(
        "--file", "-f",
        default=DEFAULT_FILE,
        help=f"Path to the expenses CSV file (default: {DEFAULT_FILE})",
    )
    args = parser.parse_args()
    main(filename=args.file)