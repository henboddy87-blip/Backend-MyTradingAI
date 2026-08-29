import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.core.logging import logger

class TelegramService:
    @staticmethod
    async def send_signal_alert(signal_dict: Dict[str, Any], chat_id: Optional[str] = None) -> bool:
        target_chat = chat_id or settings.TELEGRAM_CHAT_ID
        bot_token = settings.TELEGRAM_BOT_TOKEN

        symbol = signal_dict.get("symbol", "N/A")
        direction = signal_dict.get("direction", "BUY")
        entry = signal_dict.get("entry", 0)
        sl = signal_dict.get("stop_loss", 0)
        tp1 = signal_dict.get("take_profit_1", 0)
        tp2 = signal_dict.get("take_profit_2", 0)
        tp3 = signal_dict.get("take_profit_3", 0)
        confidence = signal_dict.get("confidence", 0)

        emoji = "🟢 🚀" if direction == "BUY" else "🔴 📉"
        message_text = (
            f"{emoji} <b>{settings.APP_NAME} AI SIGNAL ALERT</b>\n\n"
            f"<b>Asset:</b> {symbol}\n"
            f"<b>Action:</b> {direction}\n"
            f"<b>Entry:</b> {entry}\n"
            f"<b>Stop Loss:</b> {sl}\n"
            f"<b>Take Profit 1:</b> {tp1}\n"
            f"<b>Take Profit 2:</b> {tp2}\n"
            f"<b>Take Profit 3:</b> {tp3}\n"
            f"<b>Confidence:</b> {confidence}%\n\n"
            f"<i>⚠️ Automated AI alert. Not financial advice. Always apply strict risk management.</i>"
        )

        # In mock mode or when token is not set, log safely
        if not bot_token or not target_chat:
            logger.info(f"[MOCK TELEGRAM DISPATCH] Message to {target_chat or '@DemoChannel'}:\n{message_text}")
            return True

        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": target_chat,
                "text": message_text,
                "parse_mode": "HTML"
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Telegram alert delivery failed: {e}")
            return False
