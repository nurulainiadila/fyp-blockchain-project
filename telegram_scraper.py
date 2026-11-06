import os
import asyncio
from datetime import datetime
from telethon.sync import TelegramClient

# Telegram API Credentials (stored outside the code)
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

SESSION_NAME = 'investigator_session'
STORAGE_VAULT = "local_vault"

def extract_telegram_evidence(target_channel, case_id):
    """Connects to Telegram API to download messages from a public channel."""
    if not os.path.exists(STORAGE_VAULT):
        os.makedirs(STORAGE_VAULT)

    # Format the channel username safely
    channel = target_channel.strip()
    if "t.me/" in channel:
        channel = channel.split("t.me/")[-1].replace("/", "")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(STORAGE_VAULT, f"{case_id}_{timestamp}_tg_chat.txt")
    
    # Manage asyncio event loop for Streamlit compatibility
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        messages = client.get_messages(channel, limit=10)
        
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"--- FORENSIC LOG: {target_channel} ---\n")
            f.write(f"Case ID: {case_id} | Extracted: {timestamp}\n\n")
            
            for msg in messages:
                sender = msg.sender_id
                date = msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else "N/A"
                text = msg.text or "[Media/No Text]"
                f.write(f"[{date}] Sender {sender}: {text}\n")

    return {
        "case_id": case_id,
        "target_url": target_channel,
        "title": f"Telegram: {target_channel}",
        "screenshot_path": log_path,
        "extraction_date": timestamp
    }