from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3
import joblib
import pandas as pd

app = Flask(__name__)
app.secret_key = 'change-this-to-something-random-and-secret'

model = joblib.load('model/habari_model.pkl')
scaler = joblib.load('model/habari_scaler.pkl')

def get_db():
    return sqlite3.connect('habari_customers.db')

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
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['username'] = username
            session['full_name'] = user[3] if len(user) > 3 and user[3] else username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('full_name', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    at_risk = conn.execute('''
        SELECT customer_id, region, tenure_months, network_downtime_tickets,
               total_tickets_6mo, churn_probability, contact_status
        FROM customers
        WHERE churn_result = 1
        ORDER BY churn_probability DESC
        LIMIT 20
    ''').fetchall()
    total_customers = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    total_at_risk = conn.execute('SELECT COUNT(*) FROM customers WHERE churn_result = 1').fetchone()[0]
    prediction_count = conn.execute('SELECT COUNT(*) FROM history').fetchone()[0]
    conn.close()

    return render_template('dashboard.html', active='dashboard',
                            prediction_count=prediction_count,
                            at_risk=at_risk,
                            total_customers=total_customers,
                            total_at_risk=total_at_risk)

@app.route('/regions')
@login_required
def regions():
    conn = get_db()
    rows = conn.execute('''
        SELECT region,
               COUNT(*) as total,
               SUM(churn_result) as at_risk_count,
               ROUND(AVG(network_downtime_tickets), 2) as avg_downtime,
               ROUND(AVG(total_tickets_6mo), 2) as avg_tickets
        FROM customers
        GROUP BY region
        ORDER BY at_risk_count DESC
    ''').fetchall()

    total_at_risk = conn.execute('SELECT SUM(churn_result) FROM customers').fetchone()[0]
    total_customers = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
    overall_at_risk_pct = (total_at_risk / total_customers) * 100
    conn.close()

    region_data = []
    for r in rows:
        region, total, at_risk_count, avg_downtime, avg_tickets = r
        at_risk_pct = round((at_risk_count / total) * 100, 1) if total else 0
        needs_attention = at_risk_pct > (overall_at_risk_pct + 3)
        region_data.append({
            'region': region, 'total': total, 'at_risk_count': at_risk_count,
            'at_risk_pct': at_risk_pct, 'avg_downtime': avg_downtime,
            'avg_tickets': avg_tickets, 'needs_attention': needs_attention
        })

    return render_template('regions.html', active='regions', regions=region_data)

@app.route('/accountability')
@login_required
def accountability():
    conn = get_db()

    status_counts = conn.execute('''
        SELECT contact_status, COUNT(*) FROM customers
        WHERE churn_result = 1
        GROUP BY contact_status
    ''').fetchall()

    responded = conn.execute('''
        SELECT flagged_at, status_updated_at FROM customers
        WHERE churn_result = 1 AND status_updated_at IS NOT NULL AND flagged_at IS NOT NULL
    ''').fetchall()

    response_times = []
    for flagged_at, updated_at in responded:
        try:
            t1 = datetime.strptime(flagged_at, '%Y-%m-%d %H:%M')
            t2 = datetime.strptime(updated_at, '%Y-%m-%d %H:%M')
            diff_minutes = (t2 - t1).total_seconds() / 60
            if diff_minutes >= 0:
                response_times.append(diff_minutes)
        except ValueError:
            pass

    avg_response = round(sum(response_times) / len(response_times), 1) if response_times else None

    by_officer = conn.execute('''
        SELECT updated_by, COUNT(*) as actions,
               SUM(CASE WHEN contact_status = 'Resolved' THEN 1 ELSE 0 END) as resolved
        FROM customers
        WHERE updated_by IS NOT NULL
        GROUP BY updated_by
        ORDER BY actions DESC
    ''').fetchall()

    conn.close()

    return render_template('accountability.html', active='accountability',
                            status_counts=status_counts,
                            avg_response=avg_response,
                            responded_count=len(response_times),
                            by_officer=by_officer)

@app.route('/at-risk')
@login_required
def at_risk_list():
    conn = get_db()

    region_filter = request.args.get('region', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'risk')

    query = '''
        SELECT customer_id, region, package, tenure_months, network_downtime_tickets,
               total_tickets_6mo, churn_probability, contact_status
        FROM customers
        WHERE churn_result = 1
    '''
    params = []

    if region_filter:
        query += ' AND region = ?'
        params.append(region_filter)

    if search:
        query += ' AND customer_id LIKE ?'
        params.append(f'%{search}%')

    if sort_by == 'tenure':
        query += ' ORDER BY tenure_months ASC'
    elif sort_by == 'package':
        query += ' ORDER BY package ASC'
    else:
        query += ' ORDER BY churn_probability DESC'

    customers = conn.execute(query, params).fetchall()
    regions = [r[0] for r in conn.execute('SELECT DISTINCT region FROM customers ORDER BY region').fetchall()]
    conn.close()

    return render_template('at_risk_list.html', active='at_risk_list',
                            customers=customers, regions=regions,
                            selected_region=region_filter, search=search, sort_by=sort_by)

@app.route('/export-csv')
@login_required
def export_csv():
    import csv
    import io
    from flask import Response

    conn = get_db()
    region_filter = request.args.get('region', '')
    search = request.args.get('search', '')

    query = '''
        SELECT customer_id, region, package, tenure_months, network_downtime_tickets,
               total_tickets_6mo, churn_probability, contact_status
        FROM customers
        WHERE churn_result = 1
    '''
    params = []
    if region_filter:
        query += ' AND region = ?'
        params.append(region_filter)
    if search:
        query += ' AND customer_id LIKE ?'
        params.append(f'%{search}%')
    query += ' ORDER BY churn_probability DESC'

    rows = conn.execute(query, params).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Customer ID', 'Region', 'Package', 'Tenure (months)', 'Downtime Tickets',
                      'Total Tickets', 'Churn Risk (%)', 'Contact Status'])
    writer.writerows(rows)

    return Response(output.getvalue(), mimetype='text/csv',
                     headers={'Content-Disposition': 'attachment; filename=at_risk_customers.csv'})

@app.route('/customer/<customer_id>', methods=['GET', 'POST'])
@login_required
def customer_detail(customer_id):
    conn = get_db()

    if request.method == 'POST':
        new_status = request.form['contact_status']
        new_notes = request.form['notes']
        conn.execute('''
            UPDATE customers
            SET contact_status = ?, notes = ?, status_updated_at = ?, updated_by = ?
            WHERE customer_id = ?
        ''', (new_status, new_notes, datetime.now().strftime('%Y-%m-%d %H:%M'),
              session.get('full_name', session.get('username')), customer_id))
        conn.commit()

    customer = conn.execute('SELECT * FROM customers WHERE customer_id = ?', (customer_id,)).fetchone()
    columns = [desc[0] for desc in conn.execute('SELECT * FROM customers LIMIT 1').description]
    conn.close()

    customer_dict = dict(zip(columns, customer))
    return render_template('customer_detail.html', active='dashboard', customer=customer_dict)

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

        conn = get_db()
        conn.execute('''
            INSERT INTO history (time, tenure, downtime, total_tickets, fup, result, probability)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%H:%M:%S'),
            tenure, downtime_tickets, total_tickets,
            'Yes' if fup == 1 else 'No',
            'Churn' if prediction == 1 else 'Stay',
            probability
        ))
        conn.commit()
        conn.close()

    return render_template('predict.html', active='predict', prediction=prediction, probability=probability)

@app.route('/history')
@login_required
def history():
    conn = get_db()
    rows = conn.execute('SELECT time, tenure, downtime, total_tickets, fup, result, probability FROM history ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('history.html', active='history', history=rows)

if __name__ == '__main__':
    app.run(debug=True)