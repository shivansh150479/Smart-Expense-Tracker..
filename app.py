import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"
DB_FILE = "expenses.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                identifier TEXT UNIQUE NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                target_amount REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        identifier = request.form.get("identifier")
        
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM users WHERE identifier = ?", (identifier,))
            user = cursor.fetchone()
            
            if not user:
                cursor.execute("INSERT INTO users (name, identifier) VALUES (?, ?)", (name, identifier))
                conn.commit()
                user_id = cursor.lastrowid
            else:
                user_id = user[0]
                name = user[1]

            session["user_id"] = user_id
            session["user_name"] = name
            return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT b.id, b.title, b.target_amount, 
                   COALESCE(SUM(e.amount), 0) AS total_spent
            FROM budgets b
            LEFT JOIN expenses e ON b.id = e.budget_id
            WHERE b.user_id = ?
            GROUP BY b.id
            ORDER BY b.id DESC
        """, (user_id,))
        budgets = cursor.fetchall()

    return render_template("dashboard.html", user_name=session["user_name"], budgets=budgets)

@app.route("/budget/create", methods=["POST"])
def create_budget():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    title = request.form.get("title")
    target = request.form.get("target_amount", 0.0)
    
    if title:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO budgets (user_id, title, target_amount) VALUES (?, ?, ?)",
                (session["user_id"], title, float(target) if target else 0.0)
            )
            conn.commit()
            
    return redirect(url_for("dashboard"))

@app.route("/budget/<int:budget_id>", methods=["GET", "POST"])
def budget_detail(budget_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if request.method == "POST":
            if "add_expense" in request.form:
                category = request.form.get("category")
                amount = request.form.get("amount")
                note = request.form.get("note")
                if category and amount:
                    cursor.execute(
                        "INSERT INTO expenses (budget_id, category, amount, note) VALUES (?, ?, ?, ?)",
                        (budget_id, category, float(amount), note)
                    )
                    conn.commit()

            elif "delete_expense" in request.form:
                e_id = request.form.get("expense_id")
                cursor.execute("DELETE FROM expenses WHERE id = ?", (e_id,))
                conn.commit()

            return redirect(url_for("budget_detail", budget_id=budget_id))

        cursor.execute("SELECT * FROM budgets WHERE id = ? AND user_id = ?", (budget_id, session["user_id"]))
        budget = cursor.fetchone()
        
        if not budget:
            return redirect(url_for("dashboard"))

        cursor.execute("SELECT * FROM expenses WHERE budget_id = ? ORDER BY id DESC", (budget_id,))
        expenses = cursor.fetchall()
        total_spent = sum(item["amount"] for item in expenses)
        remaining = budget["target_amount"] - total_spent

    return render_template("detail.html", budget=budget, expenses=expenses, total_spent=total_spent, remaining=remaining)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
