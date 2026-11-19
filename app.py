from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import joblib
import pandas as pd

app = Flask(__name__)
app.secret_key = 'change-this-to-something-random-and-secret'

model = joblib.load('model/habari_model.pkl')
scaler = joblib.load('model/habari_scaler.pkl')

users = {
    'admin': generate_password_hash('habari123')
}

prediction_history = []

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', active='dashboard', prediction_count=len(prediction_history))

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    prediction = None
    probability = None

    if request.method == 'POST':
        tenure = float(request.form['tenure'])
        downtime_tickets = float(request.form['downtime_tickets'])
        total_tickets = float(request.form['total_tickets'])
        fup = 1 if request.form['fup'] == 'Yes' else 0

        input_data = pd.DataFrame([[tenure, downtime_tickets, total_tickets, fup]],
                                  columns=['tenure_months', 'network_downtime_tickets', 'total_tickets_6mo', 'fup_triggered'])

        input_scaled = scaler.transform(input_data)
        prediction = int(model.predict(input_scaled)[0])
        probability = round(model.predict_proba(input_scaled)[0][1] * 100, 1)

        prediction_history.insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'tenure': tenure,
            'downtime': downtime_tickets,
            'total_tickets': total_tickets,
            'fup': 'Yes' if fup == 1 else 'No',
            'result': 'Churn' if prediction == 1 else 'Stay',
            'probability': probability
        })

    return render_template('predict.html', active='predict', prediction=prediction, probability=probability)

@app.route('/history')
@login_required
def history():
    return render_template('history.html', active='history', history=prediction_history)

if __name__ == '__main__':
    app.run(debug=True)