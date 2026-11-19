# Habari Node Churn Prediction and Retention System

A web-based retention system built for Habari Node, an Internet Service Provider in Arusha, Tanzania. A Logistic Regression model trained on 2,238 real, anonymised customer records predicts which customers are at risk of churning, and the system helps retention staff act on those predictions and track their work.

## Key Results

- 83% recall on the churn class, 79.7% overall accuracy
- Network downtime complaints were the strongest predictor of churn, ahead of price or package
- Customers who churned raised nearly 3x more downtime tickets than customers who stayed

## Features

- Permanent SQLite database holding the full customer base
- Automatic churn scoring for every customer, with no manual entry
- Prioritised at-risk list, searchable, filterable, and exportable to CSV
- Customer detail page showing the ticket history behind each risk score
- Contact status and notes (Not Contacted, Contacted, Resolved, Escalated to Technical Team)
- Region-level summary with a "Needs Attention" flag
- Response-time tracking and an accountability report by individual staff member
- Individually named staff accounts with hashed passwords

## Tech Stack

Python, Pandas, Scikit-learn, Flask, SQLite, HTML/CSS, Chart.js, Werkzeug

## Setup

1. Install dependencies: `pip install flask scikit-learn joblib pandas`
2. Add your own customer CSV named `habarinode_combined.csv` to the project folder. The real Habari Node data is not included in this repository.
3. Replace every `CHANGE_ME` password in `setup_database.py` and `add_staff.py` with your own.
4. Run these scripts in order: `setup_database.py`, `add_columns.py`, `add_flagged_column.py`, `add_staff.py`, `score_customers.py`
5. Run `python app.py`, then open http://127.0.0.1:5000

## Limitations

- The churn label likely mirrors Habari Node's existing automatic rule (no payment or usage for three months), so the current predictions are not fully forward-looking. Genuine early warning would need leading-indicator data, such as days since last payment.
- Runs locally only and is not yet connected to Habari Node's live systems.

## Data Note

The model files were trained on anonymised data shared with permission. No customer records are included in this repository.

## Try It With Sample Data

The real Habari Node customer data is private and is not included in this repository. A file of 300 invented customers, `sample_data.csv`, is included so you can run the project yourself. It has the same columns as the real data, but every customer and staff name is made up.

To use it, copy the sample file to the name the setup scripts expect:

    copy sample_data.csv habarinode_combined.csv     (Windows)
    cp sample_data.csv habarinode_combined.csv       (Mac or Linux)

Then follow the setup steps above from step 3 onward. The results shown on the sample data will not match the real results reported above, because the sample data is artificial.

---

Built by Leticia Laurian Kalamata