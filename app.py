import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_FILE = "expenses.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Table for storing different budget categories/projects
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target_amount REAL DEFAULT 0.0
            )
        """)
        # Table for storing individual expenses under specific budgets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                FOREIGN KEY (budget_id) REFERENCES budgets (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    user_name = request.args.get("user_name", "")
    selected_budget_id = request.args.get("budget_id", type=int)

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if request.method == "POST":
            # Action 1: Login / Set User Name
            if "set_user" in request.form:
                name = request.form.get("user_name")
                return redirect(url_for("index", user_name=name))

            # Action 2: Create a New Budget Category (Trip, Mall, etc.)
            elif "create_budget" in request.form:
                title = request.form.get("budget_title")
                target = request.form.get("target_amount", 0.0)
                if title:
                    cursor.execute(
                        "INSERT INTO budgets (title, target_amount) VALUES (?, ?)",
                        (title, float(target) if target else 0.0)
                    )
                    conn.commit()
                    new_id = cursor.lastrowid
                    return redirect(url_for("index", user_name=user_name, budget_id=new_id))

            # Action 3: Add Expense to Selected Budget
            elif "add_expense" in request.form:
                b_id = request.form.get("budget_id")
                category = request.form.get("category")
                amount = request.form.get("amount")
                note = request.form.get("note")

                if b_id and category and amount:
                    cursor.execute(
                        "INSERT INTO expenses (budget_id, category, amount, note) VALUES (?, ?, ?, ?)",
                        (int(b_id), category, float(amount), note)
                    )
                    conn.commit()
                return redirect(url_for("index", user_name=user_name, budget_id=b_id))

            # Action 4: Delete a Budget
            elif "delete_budget" in request.form:
                b_id = request.form.get("budget_id")
                if b_id:
                    cursor.execute("DELETE FROM budgets WHERE id = ?", (b_id,))
                    cursor.execute("DELETE FROM expenses WHERE budget_id = ?", (b_id,))
                    conn.commit()
                return redirect(url_for("index", user_name=user_name))

            # Action 5: Delete an Expense
            elif "delete_expense" in request.form:
                e_id = request.form.get("expense_id")
                b_id = request.form.get("budget_id")
                if e_id:
                    cursor.execute("DELETE FROM expenses WHERE id = ?", (e_id,))
                    conn.commit()
                return redirect(url_for("index", user_name=user_name, budget_id=b_id))

        # Fetch all budgets list
        cursor.execute("SELECT * FROM budgets ORDER BY id DESC")
        all_budgets = cursor.fetchall()

        # Fetch details for the selected budget
        current_budget = None
        expenses = []
        total_spent = 0.0
        remaining_budget = 0.0

        if selected_budget_id:
            cursor.execute("SELECT * FROM budgets WHERE id = ?", (selected_budget_id,))
            current_budget = cursor.fetchone()

            if current_budget:
                cursor.execute(
                    "SELECT * FROM expenses WHERE budget_id = ? ORDER BY id DESC",
                    (selected_budget_id,)
                )
                expenses = cursor.fetchall()
                total_spent = sum(item["amount"] for item in expenses)
                remaining_budget = current_budget["target_amount"] - total_spent

    return render_template(
        "index.html",
        user_name=user_name,
        all_budgets=all_budgets,
        current_budget=current_budget,
        expenses=expenses,
        total_spent=total_spent,
        remaining_budget=remaining_budget
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
