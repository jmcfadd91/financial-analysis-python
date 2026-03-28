"""GET/POST /api/notifications/config and POST /api/notifications/test."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import NotificationConfigRequest, NotificationConfigResponse
from src.db import NotificationConfigModel, get_db
from src.reporting.notifier import TelegramNotifier

router = APIRouter()


def _mask_token(token: str) -> str:
    """Return masked token, revealing only the first 4 characters."""
    if len(token) <= 4:
        return "***"
    return token[:4] + "***"


def _get_config(db: Session) -> NotificationConfigModel:
    """Return the single config row, creating it if absent."""
    config = db.query(NotificationConfigModel).filter(NotificationConfigModel.id == 1).first()
    if config is None:
        config = NotificationConfigModel(id=1, bot_token="", chat_id="", updated_at=datetime.utcnow())
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("/notifications/config", response_model=NotificationConfigResponse)
async def get_notification_config(db: Session = Depends(get_db)) -> NotificationConfigResponse:
    config = _get_config(db)
    return NotificationConfigResponse(
        bot_token_set=bool(config.bot_token),
        bot_token_masked=_mask_token(config.bot_token) if config.bot_token else "",
        chat_id=config.chat_id,
    )


@router.post("/notifications/config", response_model=NotificationConfigResponse)
async def save_notification_config(
    req: NotificationConfigRequest, db: Session = Depends(get_db)
) -> NotificationConfigResponse:
    config = _get_config(db)
    config.bot_token = req.bot_token.strip()
    config.chat_id = req.chat_id.strip()
    config.updated_at = datetime.utcnow()
    db.commit()

    return NotificationConfigResponse(
        bot_token_set=True,
        bot_token_masked=_mask_token(config.bot_token),
        chat_id=config.chat_id,
    )


@router.post("/notifications/test")
async def send_test_notification(db: Session = Depends(get_db)) -> dict:
    config = _get_config(db)

    if not config.bot_token or not config.chat_id:
        raise HTTPException(
            status_code=422,
            detail="Telegram credentials not configured. Save bot_token and chat_id first.",
        )

    notifier = TelegramNotifier(config.bot_token, config.chat_id)
    ok = notifier.send_message(
        "✅ *Test message from Financial Analysis App* — Telegram notifications are working!"
    )

    if not ok:
        raise HTTPException(
            status_code=502,
            detail="Failed to send Telegram message. Check your bot token and chat ID.",
        )

    return {"status": "sent"}
