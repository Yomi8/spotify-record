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
    cursor.execute("SELECT * FROM Core_Users")
    users = cursor.fetchall()
    cursor.close()
    return jsonify(users)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
