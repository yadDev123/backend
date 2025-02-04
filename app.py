from flask import Flask, request, jsonify
import requests
import os
import threading

app = Flask(__name__)

DISCORD_API = "https://discord.com/api/v8"

@app.route('/test', methods=['GET'])
def test_handler():
    print("/test endpoint hit", flush=True)
    return "Hello, World!", 200

@app.route('/send', methods=['POST'])
def send_message():
    print("/send endpoint hit", flush=True)
    
    try:
        data = request.json
        print(f"Received data: {data}", flush=True)
        
        token = data.get("token")
        webhook_message = data.get("webhook_message")
        dm_message = data.get("dm_message")
        webhook_url = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"  # Replace with your webhook

        # Validate input
        if not token or not webhook_message or not dm_message:
            print("Missing required fields in payload", flush=True)
            return jsonify({"error": "Missing required fields"}), 400

        # Send to webhook
        if "@everyone" in webhook_message or "@here" in webhook_message:
            print("Blocked message containing @everyone or @here", flush=True)
            return jsonify({"error": "Message contains @everyone or @here"}), 400
        
        webhook_response = requests.post(webhook_url, json={"content": webhook_message})
        print(f"Webhook response: {webhook_response.status_code}", flush=True)
        
        if webhook_response.status_code == 204:
            print("Webhook message sent successfully", flush=True)
        else:
            print(f"Failed to send webhook message: {webhook_response.status_code} - {webhook_response.text}", flush=True)
        
        # Start a new thread to send DMs
        print("Starting DM sending thread...", flush=True)
        threading.Thread(target=send_dms, args=(token, dm_message)).start()
        
        return jsonify({"message": "Message sent to webhook and DMs"})
    
    except Exception as e:
        print(f"Error in /send endpoint: {e}", flush=True)
        return jsonify({"error": "Internal Server Error"}), 500

def send_dms(token, message):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        print("Fetching DM channels...", flush=True)
        
        response = requests.get(f"{DISCORD_API}/users/@me/channels", headers=headers)
        print(f"DM Channel Fetch Response: {response.status_code}", flush=True)

        if response.status_code != 200:
            print(f"Failed to get DM channels: {response.status_code} - {response.text}", flush=True)
            return
        
        channels = response.json()
        print(f"Fetched {len(channels)} DM channels", flush=True)
        
        for channel in channels:
            channel_id = channel.get("id")
            if channel_id:
                msg_response = requests.post(
                    f"{DISCORD_API}/channels/{channel_id}/messages",
                    headers=headers,
                    json={"content": message}
                )
                print(f"DM Response ({channel_id}): {msg_response.status_code}", flush=True)
                
                if msg_response.status_code == 200:
                    print(f"Message sent to DM: {channel_id}", flush=True)
                else:
                    print(f"Failed to send message to {channel_id}: {msg_response.status_code} - {msg_response.text}", flush=True)
    except Exception as e:
        print(f"Error in send_dms function: {e}", flush=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"Server starting on port {port}", flush=True)
    app.run(host='0.0.0.0', port=port, debug=True)
