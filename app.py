import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_FILE = "expenses.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY,
                amount REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM budget")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO budget (id, amount) VALUES (1, 0.0)")
        conn.commit()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if request.method == "POST":
            # Set or Update Budget
            if "set_budget" in request.form:
                new_budget = request.form.get("budget")
                if new_budget:
                    cursor.execute("UPDATE budget SET amount = ? WHERE id = 1", (float(new_budget),))
                    conn.commit()

            # Reset Budget back to 0
            elif "reset_budget" in request.form:
                cursor.execute("UPDATE budget SET amount = 0.0 WHERE id = 1")
                conn.commit()

            # Add Expense
            elif "add_expense" in request.form:
                category = request.form.get("category")
                amount = request.form.get("amount")
                note = request.form.get("note")

                if category and amount:
                    cursor.execute(
                        "INSERT INTO expenses (category, amount, note) VALUES (?, ?, ?)",
                        (category, float(amount), note)
                    )
                    conn.commit()

            # Delete single expense by ID
            elif "delete_expense" in request.form:
                expense_id = request.form.get("expense_id")
                if expense_id:
                    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
                    conn.commit()

            # Clear all expenses
            elif "clear_all_expenses" in request.form:
                cursor.execute("DELETE FROM expenses")
                conn.commit()

            return redirect(url_for("index"))

        # Fetch saved data
        cursor.execute("SELECT amount FROM budget WHERE id = 1")
        budget = cursor.fetchone()["amount"]

        cursor.execute("SELECT id, category, amount, note FROM expenses ORDER BY id DESC")
        expenses = cursor.fetchall()

        total_spent = sum(item["amount"] for item in expenses)
        remaining_budget = budget - total_spent

    return render_template(
        "index.html",
        expenses=expenses,
        budget=budget,
        total_spent=total_spent,
        remaining_budget=remaining_budget
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
