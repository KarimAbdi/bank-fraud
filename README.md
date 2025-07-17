# 🏦 Bank Fraud Detection System

A Python-based fraud detection system that analyzes recent bank transactions stored in a Microsoft SQL Server database and flags potentially fraudulent activity using rule-based logic.
### project structure
bank-fraud/
├── app.py                 # Main Python fraud detection script
├── setup_bankdb.sql       # SQL script to set up BankDB with tables and sample data
├── README.md              # This documentation file



##  Features

- Connects to SQL Server using `pyodbc`
- Fetches recent transactions (within the last 24 hours)
- Applies fraud detection rules:
  -  Transactions over $5000
  - Transactions outside customer’s home country
  - Multiple transactions within 60 seconds by the same customer
- Logs flagged frauds into a `FraudAlerts` table
- Displays results in a clean tabular format using `tabulate`

---

##  Tech Stack

- Python 3
- SQL Server
- `pyodbc` for database connection
- `pandas` for data processing
- `tabulate` for console tables

---

##  Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/KarimAbdi/bank-fraud
cd bank-fraud.
 
 
 ### 2. install dependencies

 pip install pyodbc pandas tabulate
