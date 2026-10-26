import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.json")
CATEGORIES = ["Food", "Rent", "Travel", "Shopping", "Bills", "Health", "Entertainment", "Gifts", "Other"]

CUR = "₹"


def normalize_data(data):
    if not isinstance(data, dict):
        return {"current": new_month_record(0), "history": []}

    current = data.get("current")
    if not isinstance(current, dict):
        current = new_month_record(0)

    history = data.get("history")
    if not isinstance(history, list):
        history = []

    current.setdefault("month", datetime.now().strftime("%B %Y"))
    current.setdefault("starting_balance", 0)
    current.setdefault("expenses", [])

    return {"current": current, "history": history}


def load():
    if not os.path.exists(DATA_FILE):
        return None

    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    return normalize_data(data)


def save(data):
    data = normalize_data(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def money(value):
    return f"{CUR}{value:,.2f}"


def ask_amount(prompt, allow_zero=False):
    while True:
        try:
            value = float(input(prompt).replace(",", ""))
            if value > 0 or (allow_zero and value == 0):
                return round(value, 2)
        except ValueError:
            pass
        print("  Please enter a valid amount.")


def new_month_record(balance):
    return {"month": datetime.now().strftime("%B %Y"), "starting_balance": balance, "expenses": []}


def spent(month):
    expenses = month.get("expenses", []) if isinstance(month, dict) else []
    return sum(float(e.get("amount", 0)) for e in expenses)


def show_month(month, title):
    month = normalize_data({"current": month, "history": []})["current"]
    total = spent(month)
    print(f"\n=== {title}: {month['month']} ===")
    print(f"Starting balance : {money(month['starting_balance'])}")
    print(f"Total spent      : {money(total)}")
    print(f"Remaining        : {money(month['starting_balance'] - total)}")
    expenses = month.get("expenses", [])
    if not expenses:
        print("\nNo expenses yet.")
        return
    print(f"\n{'#':<3} {'Date':<11} {'Time':<9} {'Category':<14} {'Amount':>13}  Description")
    for i, e in enumerate(expenses, 1):
        print(f"{i:<3} {e.get('date', ''):<11} {e.get('time', ''):<9} {e.get('category', ''):<14} {money(float(e.get('amount', 0))):>13}  {e.get('description', '-')}")


def add_expense(data):
    month = data["current"]
    amount = ask_amount("Amount: ")
    print("Categories:")
    for i, c in enumerate(CATEGORIES, 1):
        print(f"  {i}. {c}")
    while True:
        choice = input("Choose category number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            category = CATEGORIES[int(choice) - 1]
            break
        print("  Please pick a number from the list.")
    description = input("Description: ").strip() or "-"
    now = datetime.now()
    month["expenses"].append({
        "date": now.strftime("%d-%m-%Y"),
        "time": now.strftime("%I:%M %p"),
        "amount": amount,
        "category": category,
        "description": description,
    })
    save(data)
    remaining = month["starting_balance"] - spent(month)
    print(f"Saved. Remaining balance: {money(remaining)}")
    if remaining < 0:
        print("Warning: you have spent more than your balance.")


def start_new_month(data):
    cur = data["current"]
    print(f"\nThis will close {cur['month']} and save it to history.")
    print(f"Remaining this month: {money(cur['starting_balance'] - spent(cur))}")
    if input("Continue? (y/n): ").strip().lower() != "y":
        return
    data["history"].insert(0, {**cur, "total_spent": spent(cur),
                               "remaining": cur["starting_balance"] - spent(cur)})
    balance = ask_amount("Starting balance for the new month: ", allow_zero=True)
    data["current"] = new_month_record(balance)
    save(data)
    print("New month started. The old month is saved in history.")


def show_history(data):
    history = data["history"]
    if not history:
        print("\nNo history yet. Past months appear here after you start a new month.")
        return
    print("\n=== History ===")
    for i, h in enumerate(history, 1):
        print(f"{i}. {h['month']:<15} Start {money(h['starting_balance'])} | "
              f"Spent {money(h['total_spent'])} | Left {money(h['remaining'])}")
    choice = input("\nEnter a number to see that month's expenses (or press Enter to go back): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(history):
        show_month(history[int(choice) - 1], "History")


def main():
    data = load()
    if data is None:
        print("Welcome! Let's set up your first month.")
        balance = ask_amount("Starting balance for this month: ", allow_zero=True)
        data = {"current": new_month_record(balance), "history": []}
        save(data)

    while True:
        print("\n--- EXPENSE TRACKER ---")
        print("1. Add expense")
        print("2. View this month")
        print("3. Start new month")
        print("4. History")
        print("5. Exit")
        choice = input("Choose: ").strip()
        if choice == "1":
            add_expense(data)
        elif choice == "2":
            show_month(data["current"], "This month")
        elif choice == "3":
            start_new_month(data)
        elif choice == "4":
            show_history(data)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Please choose 1 to 5.")


if __name__ == "__main__":
    main()