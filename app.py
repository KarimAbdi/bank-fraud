from flask import Flask, request, jsonify
from flask_cors import CORS
from fraud_detector import FraudDetector
import logging
from datetime import datetime
import pyodbc

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

@app.route('/api/fraud-detection', methods=['POST'])
def detect_fraud():
    try:
        data = request.get_json()
        server = data.get("server")
        database = data.get("database")
        username = data.get("username")
        password = data.get("password")

        if not all([server, database, username, password]):
            return jsonify({"error": "Missing database connection details"}), 400

        logging.info(f"[{datetime.now().strftime('%Y%m%d%H%M%S')}] Start fraud detection")
        logging.info(f"Connecting to server={server}, database={database}, user={username}")

        detector = FraudDetector(server, database, username, password)
        transactions, alerts = detector.detect_fraud()

        summary = {
            "total": len(transactions),
            "alerts": len(alerts),
            "high_risk": sum(1 for a in alerts if "high" in a["Rule"].lower()),
            "recent": sorted(alerts, key=lambda x: x["TransactionDate"], reverse=True)[:5]
        }

        return jsonify({
            "transactions": transactions,
            "alerts": alerts,
            "summary": summary
        })

    except Exception as e:
        logging.error(f"❌ Error during fraud detection: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/cases', methods=['GET'])
def get_cases():
    try:
        server = request.args.get("server")
        database = request.args.get("database")
        username = request.args.get("username")
        password = request.args.get("password")

        if not all([server, database, username, password]):
            return jsonify({"error": "Missing DB credentials"}), 400

        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Cases")
        columns = [col[0] for col in cursor.description]
        cases = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(cases)

    except Exception as e:
        logging.error(f"❌ Error fetching cases: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/cases', methods=['POST'])
def add_case_v1():
    try:
        data = request.get_json()
        server = data.get("server")
        database = data.get("database")
        username = data.get("username")
        password = data.get("password")
        case = data.get("case")

        if not all([server, database, username, password, case]):
            return jsonify({"error": "Missing data"}), 400

        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Cases (CustomerID, RuleName, CaseDetails, FileName, CreatedAt)
            VALUES (?, ?, ?, ?, GETDATE())
        """, case["CustomerID"], case["Rule"], case["CaseDetails"], case.get("FileName", ""))
        conn.commit()

        return jsonify({"message": "Case added successfully"})

    except Exception as e:
        logging.error(f"❌ Error adding case v1: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/add-case', methods=['POST'])
def add_case_v2():
    try:
        data = request.get_json()
        server = data.get("server")
        database = data.get("database")
        username = data.get("username")
        password = data.get("password")

        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
        )
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Cases (TransactionID, CustomerID, FullName, RuleName, CaseDetails, TransactionDate, FileName, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
        """, data["TransactionID"], data["CustomerID"], data["FullName"],
             data["Rule"], data["Details"], data["TransactionDate"], data.get("FileName", ""))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Case added from alert page"}), 200

    except Exception as e:
        logging.error(f"❌ Error in /api/add-case: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "running"})


if __name__ == '__main__':
    app.run(debug=True)
