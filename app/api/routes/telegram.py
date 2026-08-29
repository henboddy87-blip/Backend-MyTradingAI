from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.models import TelegramAccount, User
from app.services.telegram_service import TelegramService
from app.config import settings

router = APIRouter(prefix="/telegram", tags=["Telegram Integration"])

@router.get("/status")
def get_telegram_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tg = db.query(TelegramAccount).filter(TelegramAccount.user_id == current_user.id).first()
    return {
        "is_connected": tg.is_verified if tg else False,
        "telegram_username": tg.telegram_username if tg else current_user.telegram_username,
        "chat_id": tg.chat_id if tg else None,
        "notifications_enabled": tg.notifications_enabled if tg else True,
        "bot_username": settings.TELEGRAM_USERNAME,
        "is_mock_mode": not bool(settings.TELEGRAM_BOT_TOKEN)
    }

@router.post("/connect")
def connect_telegram(
    telegram_username: str = Body(..., embed=True),
    chat_id: str = Body(None, embed=True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tg = db.query(TelegramAccount).filter(TelegramAccount.user_id == current_user.id).first()
    if not tg:
        tg = TelegramAccount(
            user_id=current_user.id,
            telegram_username=telegram_username,
            chat_id=chat_id or f"mock_chat_{current_user.id}",
            is_verified=True,
            notifications_enabled=True
        )
        db.add(tg)
    else:
        tg.telegram_username = telegram_username
        if chat_id:
            tg.chat_id = chat_id
        tg.is_verified = True

    current_user.telegram_username = telegram_username
    db.commit()
    return {"message": "Telegram notifications successfully connected"}

@router.post("/test-alert")
async def send_test_alert(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    sample_signal = {
        "symbol": "XAUUSD",
        "direction": "BUY",
        "entry": 2654.50,
        "stop_loss": 2642.00,
        "take_profit_1": 2672.00,
        "take_profit_2": 2685.00,
        "take_profit_3": 2700.00,
        "confidence": 84.5
    }
    
    tg = db.query(TelegramAccount).filter(TelegramAccount.user_id == current_user.id).first()
    chat_id = tg.chat_id if tg else None
    
    success = await TelegramService.send_signal_alert(sample_signal, chat_id=chat_id)
    return {
        "status": "sent" if success else "failed",
        "message": "Test alert dispatched to Telegram stream (check server logs or bot channel)."
    }
