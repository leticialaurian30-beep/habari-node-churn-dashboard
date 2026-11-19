# Habari Node Churn Prediction Dashboard

An AI-powered web dashboard that predicts customer churn for Habari Node, a real Internet Service Provider based in Arusha, Tanzania. Built and trained on 2,238 real, anonymised customer records shared directly by the company.

## The Problem

Internet Service Providers lose customers to unresolved technical problems, usually without warning. This project identifies customers at risk of leaving before they actually cancel their service.

## Key Result

- **83% recall** — the model correctly identifies 83 out of every 100 customers who go on to churn
- **79.7% overall accuracy**
- The strongest predictor of churn was **network downtime complaints**, not price or plan: customers who churned had raised nearly 3x more downtime tickets than customers who stayed

## Features

- Secure staff login with hashed passwords (no plain-text passwords, ever)
- Real-time churn prediction for individual customers
- Analytics dashboard with live churn statistics and charts
- Automatic prediction history log

## Tech Stack

**Data & Modelling:** Python, Pandas, Scikit-learn, Google Colab, Logistic Regression
**Web & Delivery:** Flask, HTML/CSS, Chart.js, Werkzeug (password hashing)



## Note on Data

The model files included here (`model/habari_model.pkl`, `model/habari_scaler.pkl`) were trained on anonymised customer data shared with permission. No personally identifiable customer information is included in this repository.

## Status

This is a working prototype. Planned improvements include bulk customer upload, a persistent database, and cloud deployment.

---
Built by Leticia Laurian