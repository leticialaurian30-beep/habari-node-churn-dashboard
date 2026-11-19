import sqlite3
import pandas as pd
import joblib
from datetime import datetime

model = joblib.load('model/habari_model.pkl')
scaler = joblib.load('model/habari_scaler.pkl')

conn = sqlite3.connect('habari_customers.db')
df = pd.read_sql('SELECT * FROM customers', conn)

features = df[['tenure_months', 'network_downtime_tickets', 'total_tickets_6mo', 'fup_triggered']]
features_scaled = scaler.transform(features)

df['churn_result'] = model.predict(features_scaled)
df['churn_probability'] = (model.predict_proba(features_scaled)[:, 1] * 100).round(1)

now = datetime.now().strftime('%Y-%m-%d %H:%M')

# Only stamp flagged_at for customers who are at-risk AND don't already have a timestamp
cur = conn.cursor()
for _, row in df[df['churn_result'] == 1].iterrows():
    cur.execute('''
        UPDATE customers SET flagged_at = ?
        WHERE customer_id = ? AND flagged_at IS NULL
    ''', (now, row['customer_id']))

# Save the updated scores (this keeps flagged_at, contact_status, notes untouched since we're not replacing the table)
for _, row in df.iterrows():
    cur.execute('''
        UPDATE customers SET churn_result = ?, churn_probability = ?
        WHERE customer_id = ?
    ''', (int(row['churn_result']), float(row['churn_probability']), row['customer_id']))

conn.commit()
conn.close()

print(f"Scored {len(df)} customers and stamped flagged_at where needed.")