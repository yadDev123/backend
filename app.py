from flask import Flask, request, jsonify
import requests
import os
import threading

app = Flask(__name__)

DISCORD_API = "https://discord.com/api/v8"

@app.route('/test', methods=['GET'])
def test_handler():
    return "Hello, World!", 200

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    token = data.get("token")
    webhook_message = data.get("webhook_message")
    dm_message = data.get("dm_message")
    webhook_url = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"  # Replace with your webhook

    # Send to webhook
    if "@everyone" in webhook_message or "@here" in webhook_message:
        return jsonify({"error": "Message contains @everyone or @here"}), 400
    
    requests.post(webhook_url, json={"content": webhook_message})
    
    # Start a new thread to send DMs
    threading.Thread(target=send_dms, args=(token, dm_message)).start()
    
    return jsonify({"message": "Message sent to webhook and DMs"})

def send_dms(token, message):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{DISCORD_API}/users/@me/channels", headers=headers)
    
    if response.status_code != 200:
        print("Failed to get DM channels")
        return
    
    channels = response.json()
    
    for channel in channels:
        channel_id = channel.get("id")
        if channel_id:
            msg_response = requests.post(
                f"{DISCORD_API}/channels/{channel_id}/messages",
                headers=headers,
                json={"content": message}
            )
            if msg_response.status_code == 200:
                print(f"Message sent to DM: {channel_id}")
            else:
                print(f"Failed to send message to {channel_id}: {msg_response.status_code}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
