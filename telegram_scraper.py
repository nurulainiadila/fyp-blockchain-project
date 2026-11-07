
import os
import asyncio
from datetime import datetime
from telethon.sync import TelegramClient

SESSION_NAME = "investigator_session"
STORAGE_VAULT = "local_vault"


def extract_telegram_evidence(target_channel, case_id):
    """Collect recent messages from a public Telegram channel."""

    # Read credentials from environment variables
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        raise ValueError(
            "Telegram API credentials are missing. "
            "Please configure TELEGRAM_API_ID and TELEGRAM_API_HASH."
        )

    try:
        api_id = int(api_id)
    except ValueError:
        raise ValueError("TELEGRAM_API_ID must be a number.")

    os.makedirs(STORAGE_VAULT, exist_ok=True)

    # Format public channel username
    channel = target_channel.strip()
    if "t.me/" in channel:
        channel = channel.split("t.me/")[-1].strip("/")
    channel = channel.lstrip("@")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(
        STORAGE_VAULT,
        f"{case_id}_{timestamp}_tg_chat.txt"
    )

    # Prepare event loop for Streamlit
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Connect to Telegram
    with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
        messages = client.get_messages(channel, limit=10)

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"--- FORENSIC LOG: {target_channel} ---\n")
            f.write(f"Case ID: {case_id} | Extracted: {timestamp}\n\n")

            for msg in messages:
                sender = msg.sender_id
                date = (
                    msg.date.strftime("%Y-%m-%d %H:%M:%S")
                    if msg.date else "N/A"
                )
                message_text = msg.text or "[Media/No Text]"

                f.write(
                    f"[{date}] Sender {sender}: {message_text}\n"
                )

    return {
        "case_id": case_id,
        "target_url": target_channel,
        "title": f"Telegram: {target_channel}",
        "screenshot_path": log_path,
        "extraction_date": timestamp
    }

