from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Single global storage for all budget entries
budgets = []

@app.route('/')
def dashboard():
    return render_template('dashboard.html', budgets=budgets)

@app.route('/add-budget', methods=['POST'])
def add_budget():
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', '').strip()
    
    if title and amount:
        budget_id = len(budgets) + 1
        budgets.append({
            "id": budget_id,
            "title": title,
            "amount": float(amount)
        })
        
    return redirect(url_for('dashboard'))

@app.route('/detail/<int:budget_id>')
def detail(budget_id):
    budget = next((b for b in budgets if b['id'] == budget_id), None)
    if not budget:
        return redirect(url_for('dashboard'))
    return render_template('detail.html', budget=budget)

if __name__ == '__main__':
    app.run(debug=True)
