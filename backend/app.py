from flask import Flask, request, jsonify
import mysql.connector
import json
import os

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'  # create this folder

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="recordserver",
    password="$3000JHCpaperPC",
    database="spotifydb"
)

cursor = db.cursor()

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "OK", "message": "Test successful"}), 200

@app.route('/api/status', methods=['GET'])
def db_status():
    try:
        cursor.execute("SELECT 1")
        return jsonify({"status": "OK", "message": "Database connected"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route('/api/users')
def get_users():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM core_users")
    users = cursor.fetchall()
    cursor.close()
    return jsonify(users)

@app.route('/api/users/sync', methods=['POST'])
def sync_user():
    data = request.get_json()

    required_fields = ['auth0_id', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "ERROR", "message": "Missing required fields"}), 400

    auth0_id = data['auth0_id']
    email = data['email']
    username = data.get('username', None)
    show_explicit = int(data.get('show_explicit', 1))
    dark_mode = int(data.get('dark_mode', 0))

    try:
        cursor = db.cursor()
        # Insert or update user
        query = """
        INSERT INTO core_users (auth0_id, email, username, show_explicit, dark_mode)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            email = VALUES(email),
            username = VALUES(username),
            show_explicit = VALUES(show_explicit),
            dark_mode = VALUES(dark_mode)
        """
        cursor.execute(query, (auth0_id, email, username, show_explicit, dark_mode))
        db.commit()
        cursor.close()
        return jsonify({"status": "OK", "message": "User synced successfully"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
