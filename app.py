import pyodbc
import pandas as pd
from datetime import datetime, timedelta
from tabulate import tabulate

class FraudDetector:
    def __init__(self, server, database, username, password):
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
        )
        self.conn = None

    def connect(self):
        try:
            self.conn = pyodbc.connect(self.connection_string)
            print(" Connected to SQL Server")
            return True
        except Exception as e:
            print(f" Connection error: {e}")
            return False

    def disconnect(self):
        if self.conn:
            self.conn.close()
            print(" Disconnected")

    def fetch_transactions(self):
        cutoff_time = datetime.now() - timedelta(hours=24)
        query = """
    SELECT 
        t.TransactionID, t.CustomerID, c.FullName, c.Country AS HomeCountry,
        t.Amount, t.TransactionDate, t.Location
    FROM Transactions t
    JOIN Customers c ON t.CustomerID = c.CustomerID
    WHERE t.TransactionDate >= ?
    ORDER BY t.CustomerID, t.TransactionDate
"""

        try:
            return pd.read_sql(query, self.conn, params=[cutoff_time])
        except Exception as e:
            print(f" Failed to fetch transactions: {e}")
            return None

    def detect_fraud(self, df):
        if df is None or df.empty:
            return []

        alerts = []

        # High Amount Rule
        high_amt = df[df['Amount'] > 5000]
        for _, row in high_amt.iterrows():
            alerts.append({
                'TransactionID': row['TransactionID'],
                'CustomerID': row['CustomerID'],
                'Rule': 'High Amount',
                'Details': f"Amount ${row['Amount']:.2f} exceeds $5000"
            })

        # Foreign Location Rule
        df['IsForeign'] = df.apply(
            lambda x: pd.notna(x['Location']) and x['Location'].strip() != x['HomeCountry'].strip(),
            axis=1
        )
        for _, row in df[df['IsForeign']].iterrows():
            alerts.append({
                'TransactionID': row['TransactionID'],
                'CustomerID': row['CustomerID'],
                'Rule': 'Foreign Location',
                'Details': f"Transaction in {row['Location']} (home: {row['HomeCountry']})"
            })

        # Rapid Transaction Rule
        df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
        df = df.sort_values(['CustomerID', 'TransactionDate'])
        df['TimeDiff'] = df.groupby('CustomerID')['TransactionDate'].diff().dt.total_seconds()
        for _, row in df[(df['TimeDiff'] < 60) & (df['TimeDiff'] > 0)].iterrows():
            alerts.append({
                'TransactionID': row['TransactionID'],
                'CustomerID': row['CustomerID'],
                'Rule': 'Rapid Transactions',
                'Details': f"Another transaction within {row['TimeDiff']} seconds"
            })

        return alerts

    def save_alerts(self, alerts):
        if not alerts:
            print(" No alerts to save.")
            return

        cursor = self.conn.cursor()
        saved = 0
        for alert in alerts:
            try:
                cursor.execute("""
                INSERT INTO FraudAlerts (TransactionID, CustomerID, Reason)
                VALUES (?, ?, ?)""",
                alert['TransactionID'],
                alert['CustomerID'],
                f"{alert['Rule']}: {alert['Details']}"
                )
                saved += 1
            except Exception as e:
                print(f" Failed to save alert {alert['TransactionID']}: {e}")
        self.conn.commit()
        print(f" Saved {saved} alerts.")

def main():
    print("\n===  Python Fraud Detection System ===")
    server = input("SQL Server [localhost]: ") or 'localhost'
    username = input("Username [SA]: ") or 'SA'
    password = input("Password: ")

    detector = FraudDetector(server, 'bankdb', username, password)

    if not detector.connect():
        return

    try:
        df = detector.fetch_transactions()
        if df is not None:
            print(f"\n Checking {len(df)} transactions...")
            alerts = detector.detect_fraud(df)

            if alerts:
                print(f"\n Detected {len(alerts)} fraud cases:")
                print(tabulate(pd.DataFrame(alerts), headers='keys', tablefmt='fancy_grid'))
                detector.save_alerts(alerts)
            else:
                print(" No suspicious activity found.")
    finally:
        detector.disconnect()
        print("\n Analysis complete.")

if __name__ == "__main__":
    main()
