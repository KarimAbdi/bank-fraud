import pyodbc
from datetime import datetime, timedelta
import math

class FraudDetector:
    def __init__(self, server, database, username, password):
        self.conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        self.cursor = self.conn.cursor()

    def get_transactions(self):
        self.cursor.execute("SELECT * FROM Transactions")
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_customer_name(self, customer_id):
        self.cursor.execute("SELECT FullName FROM Customers WHERE CustomerID = ?", customer_id)
        row = self.cursor.fetchone()
        return row[0] if row else "Unknown"

    def save_alert(self, alert):
        try:
            self.cursor.execute("""
                INSERT INTO FraudAlerts (TransactionID, CustomerID, FullName, RuleName, Details, TransactionDate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert['TransactionID'],
                alert['CustomerID'],
                alert['FullName'],
                alert['Rule'],
                alert['Details'],
                alert['TransactionDate']
            ))
            self.conn.commit()
        except Exception as e:
            print(f"❌ Failed to save alert: {e}")

    def haversine(self, lat1, lon1, lat2, lon2):
        if None in [lat1, lon1, lat2, lon2]:
            return 0
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def detect_fraud(self):
        txns = self.get_transactions()
        alerts = []
        for t in txns:
            t['FullName'] = self.get_customer_name(t['CustomerID'])

        # Rule 1: ATM velocity + geodistance
        for i, t1 in enumerate(txns):
            if t1['TransactionType'] == 'ATM':
                for t2 in txns[i+1:]:
                    if t1['CustomerID'] == t2['CustomerID'] and t2['TransactionType'] == 'ATM':
                        time_diff = abs((t2['TransactionDate'] - t1['TransactionDate']).total_seconds() / 60)
                        distance = self.haversine(t1['Latitude'], t1['Longitude'], t2['Latitude'], t2['Longitude'])
                        if time_diff <= 60 and distance > 100:
                            alerts.append({
                                "TransactionID": t2['TransactionID'],
                                "CustomerID": t2['CustomerID'],
                                "FullName": t2['FullName'],
                                "Rule": "Velocity + Geo",
                                "Details": f"Two ATM txns within {time_diff:.1f} mins, {distance:.1f} km apart",
                                "TransactionDate": t2['TransactionDate']
                            })

        # Rule 2: Structuring
        for cust in set(t['CustomerID'] for t in txns):
            transfers = [t for t in txns if t['CustomerID'] == cust and t['TransactionType'] == 'Mobile-Money']
            for i in range(len(transfers)):
                window = [transfers[i]]
                for j in range(i + 1, len(transfers)):
                    if (transfers[j]['TransactionDate'] - transfers[i]['TransactionDate']).total_seconds() <= 7200:
                        window.append(transfers[j])
                grouped = {}
                for t in window:
                    if t['PayeeID']:
                        grouped.setdefault(t['PayeeID'], []).append(t)
                for payee, txlist in grouped.items():
                    if len(txlist) >= 3 and all(t['Amount'] < 100000 for t in txlist) and sum(t['Amount'] for t in txlist) >= 300000:
                        alerts.append({
                            "TransactionID": txlist[-1]['TransactionID'],
                            "CustomerID": cust,
                            "FullName": txlist[-1]['FullName'],
                            "Rule": "Structuring",
                            "Details": f"{len(txlist)} transfers to {payee} totaling KSh {sum(t['Amount'] for t in txlist):,.2f}",
                            "TransactionDate": txlist[-1]['TransactionDate']
                        })

        # Rule 3: Night-time high value
        for t in txns:
            if 0 <= t['TransactionDate'].hour < 4 and t['Amount'] >= 50000:
                alerts.append({
                    "TransactionID": t['TransactionID'],
                    "CustomerID": t['CustomerID'],
                    "FullName": t['FullName'],
                    "Rule": "Night-time high-value",
                    "Details": f"Txn at {t['TransactionDate'].strftime('%H:%M')} for KSh {t['Amount']:,.2f}",
                    "TransactionDate": t['TransactionDate']
                })

        # Rule 4: New payee large transfer
        seen = {}
        for t in sorted(txns, key=lambda x: x['TransactionDate']):
            key = (t['CustomerID'], t['PayeeID'])
            if t['PayeeID'] and key not in seen and t['Amount'] >= 1_000_000:
                alerts.append({
                    "TransactionID": t['TransactionID'],
                    "CustomerID": t['CustomerID'],
                    "FullName": t['FullName'],
                    "Rule": "New payee large transfer",
                    "Details": f"First-time transfer to {t['PayeeID']} of KSh {t['Amount']:,.2f}",
                    "TransactionDate": t['TransactionDate']
                })
            seen[key] = True

        # Rule 5: MCC = 7995 POS gambling
        for cust in set(t['CustomerID'] for t in txns):
            mcc_txns = [t for t in txns if t['CustomerID'] == cust and t['TransactionType'] == 'POS' and t['MCC'] == 7995]
            mcc_txns.sort(key=lambda t: t['TransactionDate'])
            for i in range(len(mcc_txns) - 4):
                if (mcc_txns[i+4]['TransactionDate'] - mcc_txns[i]['TransactionDate']).total_seconds() <= 86400:
                    alerts.append({
                        "TransactionID": mcc_txns[i+4]['TransactionID'],
                        "CustomerID": cust,
                        "FullName": mcc_txns[i+4]['FullName'],
                        "Rule": "High-risk MCC",
                        "Details": "≥5 gambling txns in 24 hrs",
                        "TransactionDate": mcc_txns[i+4]['TransactionDate']
                    })
                    break

        # Rule 6: POS/ATM → CNP/Online in ≤30min & >100km
        for i, t1 in enumerate(txns):
            if t1['TransactionType'] in ['POS', 'ATM']:
                for t2 in txns[i+1:]:
                    if t1['CustomerID'] == t2['CustomerID'] and t2['TransactionType'] in ['CNP', 'Online']:
                        time_diff = (t2['TransactionDate'] - t1['TransactionDate']).total_seconds() / 60
                        distance = self.haversine(t1['Latitude'], t1['Longitude'], t2['Latitude'], t2['Longitude'])
                        if 0 < time_diff <= 30 and distance > 100:
                            alerts.append({
                                "TransactionID": t2['TransactionID'],
                                "CustomerID": t2['CustomerID'],
                                "FullName": t2['FullName'],
                                "Rule": "POS→CNP 30m >100km",
                                "Details": f"{t1['TransactionType']}→{t2['TransactionType']} in {time_diff:.1f}min, {distance:.1f}km apart",
                                "TransactionDate": t2['TransactionDate']
                            })

        # Rule 7: <3 txns in 90d + ≥500k
        for t in txns:
            prior = [x for x in txns if x['CustomerID'] == t['CustomerID'] and x['TransactionDate'] < t['TransactionDate'] and x['TransactionDate'] >= t['TransactionDate'] - timedelta(days=90)]
            if len(prior) < 3 and t['Amount'] >= 500000:
                alerts.append({
                    "TransactionID": t['TransactionID'],
                    "CustomerID": t['CustomerID'],
                    "FullName": t['FullName'],
                    "Rule": "<3 txns in 90d + ≥500k",
                    "Details": f"{len(prior)} txns in 90d, then KSh {t['Amount']:,.2f}",
                    "TransactionDate": t['TransactionDate']
                })

        # Rule 8: ≥3 new payees in 24h ≥200k
        for cust in set(t['CustomerID'] for t in txns):
            cust_txns = [t for t in txns if t['CustomerID'] == cust and t['PayeeID']]
            seen = set()
            firsts = []
            for t in sorted(cust_txns, key=lambda x: x['TransactionDate']):
                key = (t['CustomerID'], t['PayeeID'])
                if key not in seen:
                    seen.add(key)
                    firsts.append(t)
            for i, t in enumerate(firsts):
                window = [x for x in firsts if 0 <= (x['TransactionDate'] - t['TransactionDate']).total_seconds() <= 86400]
                if len(window) >= 3 and sum(x['Amount'] for x in window) >= 200000:
                    alerts.append({
                        "TransactionID": t['TransactionID'],
                        "CustomerID": t['CustomerID'],
                        "FullName": t['FullName'],
                        "Rule": "≥3 new payees 24h ≥200k",
                        "Details": f"{len(window)} new payees in 24h totaling KSh {sum(x['Amount'] for x in window):,.2f}",
                        "TransactionDate": t['TransactionDate']
                    })
                    break

        # Rule 9: IN cash ≥200k + OUT ≥80% in 2h
        deposits = [t for t in txns if t['TransactionType'] == 'Deposit' and float(t['Amount']) >= 200000]
        for dep in deposits:
            out_txns = [
                t for t in txns
                if t['CustomerID'] == dep['CustomerID'] and t['TransactionType'] in ['Mobile', 'Online']
                and 0 <= (t['TransactionDate'] - dep['TransactionDate']).total_seconds() <= 7200
            ]
            total_out = sum(float(t['Amount']) for t in out_txns)
            if total_out >= 0.8 * float(dep['Amount']):
                alerts.append({
                    "TransactionID": dep['TransactionID'],
                    "CustomerID": dep['CustomerID'],
                    "FullName": dep['FullName'],
                    "Rule": "IN ≥200k + OUT ≥80% in 2h",
                    "Details": f"Deposited KSh {float(dep['Amount']):,.2f}, withdrew {total_out:,.2f} in 2h",
                    "TransactionDate": dep['TransactionDate']
                })

        # Rule 10: ≥4 POS txns same round amt ≥50k in 60min
        for cust in set(t['CustomerID'] for t in txns):
            pos_txns = [t for t in txns if t['CustomerID'] == cust and t['TransactionType'] == 'POS' and float(t['Amount']) >= 50000 and float(t['Amount']) % 1000 == 0]
            pos_txns.sort(key=lambda x: x['TransactionDate'])
            for i in range(len(pos_txns) - 3):
                window = pos_txns[i:i+4]
                if all(t['Amount'] == window[0]['Amount'] for t in window) and (window[-1]['TransactionDate'] - window[0]['TransactionDate']).total_seconds() <= 3600:
                    alerts.append({
                        "TransactionID": window[-1]['TransactionID'],
                        "CustomerID": cust,
                        "FullName": window[-1]['FullName'],
                        "Rule": "4+ POS same amt in 60min",
                        "Details": f"4 POS of KSh {float(window[0]['Amount']):,.0f} in 60min",
                        "TransactionDate": window[-1]['TransactionDate']
                    })
                    break

        for alert in alerts:
            print("🚨 Alert Generated:", alert)
            self.save_alert(alert)
            alert["TransactionDate"] = alert["TransactionDate"].strftime("%Y-%m-%d %H:%M:%S")

        return txns, alerts
