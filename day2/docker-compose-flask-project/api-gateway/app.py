from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:5001')

@app.route('/api/users', methods=['GET'])
def fetch_users():
    try:
        response = requests.get(f"{USER_SERVICE_URL}/users")
        response.raise_for_status()
        return jsonify({
            "message": "Data fetched via API Gateway successfully!",
            "data": response.json()
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Could not connect to user-service", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
