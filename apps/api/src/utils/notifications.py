import requests
import os

def send_telegram_alert(message: str):
    """Envía una notificación urgente a Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print(f"⚠️ Telegram no configurado. Mensaje omitido: {message}")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"🦅 **GoalOS Alert** 🦅\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"🔥 Error enviando alerta a Telegram: {e}")