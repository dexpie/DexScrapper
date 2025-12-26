import requests
import logging

logger = logging.getLogger(__name__)

def send_discord_webhook(webhook_url, message):
    """
    Sends a message to a Discord Webhook.
    """
    if not webhook_url:
        return False
    
    data = {
        "content": message
    }
    
    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        logger.info("Discord notification sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False

def send_telegram_message(bot_token, chat_id, message):
    """
    Sends a message to a Telegram Chat.
    """
    if not bot_token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False
