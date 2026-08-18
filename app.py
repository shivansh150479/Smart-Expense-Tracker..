from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# Secret key required for managing user sessions securely
app.secret_key = 'super_secret_budget_key_123'

# SQLite Database setup to keep user data private and persistent
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model for User Budgets
class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)  # User isolation identifier
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default='General')

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username', '').strip()
        if name:
            # Set private session isolated to this specific user/browser
            session['username'] = name.title()
            session['show_welcome'] = True
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    username = session['username']
    
    # PRIVACY CRITICAL: Query ONLY budgets belonging to this user
    user_budgets = Budget.query.filter_by(username=username).order_by(Budget.id.desc()).all()
    total_amount = sum(b.amount for b in user_budgets)
    
    show_welcome = session.pop('show_welcome', False)
    
    return render_template('dashboard.html', 
                           username=username, 
                           budgets=user_budgets, 
                           total_amount=total_amount,
                           show_welcome=show_welcome)

@app.route('/add-budget', methods=['POST'])
def add_budget():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    title = request.form.get('title', '').strip()
    amount_raw = request.form.get('amount', '').strip()
    category = request.form.get('category', 'General').strip()
    
    if title and amount_raw:
        try:
            amount = float(amount_raw)
            new_budget = Budget(
                username=session['username'], # Tie budget strictly to active session user
                title=title,
                amount=amount,
                category=category if category else 'General'
            )
            db.session.add(new_budget)
            db.session.commit()
        except ValueError:
            pass
            
    return redirect(url_for('dashboard'))

@app.route('/get-budget-detail/<int:budget_id>')
def get_budget_detail(budget_id):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    # Ensure user can ONLY open modal details for their own budget entry
    budget = Budget.query.filter_by(id=budget_id, username=session['username']).first()
    if budget:
        return jsonify({
            'id': budget.id,
            'title': budget.title,
            'amount': budget.amount,
            'category': budget.category
        })
    return jsonify({'error': 'Not found'}), 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
