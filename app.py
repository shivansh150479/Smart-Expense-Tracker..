import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Secret key is required to secure session data per browser
app.secret_key = os.environ.get("SECRET_KEY", "expense-tracker-secret-key-123")

@app.route("/", methods=["GET", "POST"])
def index():
    # Initialize separate data for the current browser session
    if "expenses" not in session:
        session["expenses"] = []
    if "budget" not in session:
        session["budget"] = 0.0

    if request.method == "POST":
        # Handle setting/updating the monthly budget
        if "set_budget" in request.form:
            new_budget = request.form.get("budget")
            if new_budget:
                session["budget"] = float(new_budget)
                session.modified = True

        # Handle adding a new expense
        elif "add_expense" in request.form:
            category = request.form.get("category")
            amount = request.form.get("amount")
            note = request.form.get("note")

            if category and amount:
                expenses = session["expenses"]
                expenses.append({
                    "category": category,
                    "amount": float(amount),
                    "note": note
                })
                session["expenses"] = expenses
                session.modified = True

        return redirect(url_for("index"))

    total_spent = sum(item["amount"] for item in session["expenses"])
    remaining_budget = session["budget"] - total_spent

    return render_template(
        "index.html",
        expenses=session["expenses"],
        budget=session["budget"],
        total_spent=total_spent,
        remaining_budget=remaining_budget
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
