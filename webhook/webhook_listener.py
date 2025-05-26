from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if not request.is_json:
        return jsonify({"error": "Invalid content type, expected JSON"}), 400

    payload = request.get_json()
    print("Received webhook payload:", payload)

    try:
        # Kick off deploy.sh in background
        subprocess.Popen(['/spotify-record/webhook/deploy.sh'])
        return jsonify({"status": "deploy started"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

