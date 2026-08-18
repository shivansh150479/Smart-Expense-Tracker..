from flask import Flask, render_template, request, redirect, url_for, session, flash
import random

app = Flask(__name__)
# Secure secret key required to sign session cookies
app.secret_key = 'replace_this_with_a_secure_random_key'

# In-memory storage (Replace with a database like SQLite/PostgreSQL in production)
# Structure: { phone_number: user_id }
users_db = {} 

# Structure: { phone_number: "123456" }
otp_store = {} 

# Structure: { user_id: [ {"id": 1, "title": "Groceries", "amount": 150}, ... ] }
user_budgets_db = {} 

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        
        if not phone or len(phone) < 10:
            flash("Please enter a valid phone number.")
            return render_template('login.html')
            
        # Generate random 6-digit OTP
        otp = str(random.randint(100000, 999999))
        otp_store[phone] = otp
        
        # SIMULATION: In production, integrate an SMS gateway API here (e.g., Twilio / Fast2SMS)
        print(f"==============================")
        print(f"OTP FOR {phone} IS: {otp}")
        print(f"==============================")
        
        return render_template('verify_otp.html', phone=phone)
        
    return render_template('login.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    phone = request.form.get('phone', '').strip()
    entered_otp = request.form.get('otp', '').strip()
    
    # Validate OTP
    if phone in otp_store and otp_store[phone] == entered_otp:
        # Clear temporary OTP from memory
        del otp_store[phone]
        
        # Create user if logging in for the first time
        if phone not in users_db:
            new_user_id = len(users_db) + 1
            users_db[phone] = new_user_id
            user_budgets_db[new_user_id] = []
            
        # Assign private session variables for this specific browser context
        session['user_id'] = users_db[phone]
        session['phone'] = phone
        
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid or expired OTP. Please try again.")
        return render_template('verify_otp.html', phone=phone)

@app.route('/dashboard')
def dashboard():
    # Enforce authentication guard
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    
    # Retrieve ONLY the logged-in user's budgets
    current_user_budgets = user_budgets_db.get(user_id, [])
    
    return render_template('dashboard.html', 
                           phone=session.get('phone'), 
                           budgets=current_user_budgets)

@app.route('/add-budget', methods=['POST'])
def add_budget():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', '').strip()
    
    if title and amount:
        budget_id = len(user_budgets_db[user_id]) + 1
        user_budgets_db[user_id].append({
            "id": budget_id,
            "title": title,
            "amount": float(amount)
        })
        
    return redirect(url_for('dashboard'))

@app.route('/detail/<int:budget_id>')
def detail(budget_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user_budgets = user_budgets_db.get(user_id, [])
    
    # Ensure the user can only view their own budget details
    budget = next((b for b in user_budgets if b['id'] == budget_id), None)
    
    if not budget:
        flash("Budget item not found or unauthorized access.")
        return redirect(url_for('dashboard'))
        
    return render_template('detail.html', budget=budget, phone=session.get('phone'))

@app.route('/logout')
def logout():
    # Completely purge session data to isolate users on logout
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
