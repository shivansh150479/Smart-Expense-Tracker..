from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Single list storing all budget entries
budgets = []

@app.route('/')
def index():
    return render_template('index.html', budgets=budgets)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    total_amount = sum(b['amount'] for b in budgets)
    return render_template('dashboard.html', budgets=budgets, total_amount=total_amount)

@app.route('/add-budget', methods=['POST'])
def add_budget():
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', '').strip()
    category = request.form.get('category', 'General').strip()
    
    if title and amount:
        budget_id = len(budgets) + 1
        budgets.append({
            "id": budget_id,
            "title": title,
            "amount": float(amount),
            "category": category
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
