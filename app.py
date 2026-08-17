import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Sample expense data in Rupees
EXPENSES = [
    {"category": "Food", "amount": 1200, "note": "Groceries"},
    {"category": "Entertainment", "amount": 800, "note": "Movie Ticket"},
    {"category": "Bills", "amount": 3500, "note": "Internet & Electricity"}
]
MONTHLY_BUDGET = 10000  # Default budget in ₹

@app.route("/", methods=["GET", "POST"])
def index():
    global MONTHLY_BUDGET

    if request.method == "POST":
        # Handle setting a new budget
        if "set_budget" in request.form:
            new_budget = request.form.get("budget")
            if new_budget:
                MONTHLY_BUDGET = float(new_budget)

        # Handle adding an expense
        elif "add_expense" in request.form:
            category = request.form.get("category")
            amount = request.form.get("amount")
            note = request.form.get("note")

            if category and amount:
                EXPENSES.append({
                    "category": category,
                    "amount": float(amount),
                    "note": note
                })

        return redirect(url_for("index"))

    total_spent = sum(item["amount"] for item in EXPENSES)
    remaining_budget = MONTHLY_BUDGET - total_spent

    return render_template(
        "index.html",
        expenses=EXPENSES,
        budget=MONTHLY_BUDGET,
        total_spent=total_spent,
        remaining_budget=remaining_budget
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
