"""GET/POST /api/notifications/config and POST /api/notifications/test."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.schemas import NotificationConfigRequest, NotificationConfigResponse
from src.reporting.notifier import TelegramNotifier

router = APIRouter()

_CONFIG_PATH = Path("data/notification_config.json")


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(_CONFIG_PATH.read_text())
    except Exception:
        return {}


def _save_config(bot_token: str, chat_id: str) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps({"bot_token": bot_token, "chat_id": chat_id}))


def _mask_token(token: str) -> str:
    """Return e.g. '123456:A***xyz' — reveal first 8 and last 3 chars."""
    if len(token) <= 11:
        return "***"
    return token[:8] + "***" + token[-3:]


@router.get("/notifications/config", response_model=NotificationConfigResponse)
async def get_notification_config() -> NotificationConfigResponse:
    cfg = _load_config()
    token = cfg.get("bot_token", "")
    chat_id = cfg.get("chat_id", "")
    return NotificationConfigResponse(
        bot_token_set=bool(token),
        bot_token_masked=_mask_token(token) if token else "",
        chat_id=chat_id,
    )


@router.post("/notifications/config", response_model=NotificationConfigResponse)
async def save_notification_config(req: NotificationConfigRequest) -> NotificationConfigResponse:
    _save_config(req.bot_token.strip(), req.chat_id.strip())
    return NotificationConfigResponse(
        bot_token_set=True,
        bot_token_masked=_mask_token(req.bot_token.strip()),
        chat_id=req.chat_id.strip(),
    )


@router.post("/notifications/test")
async def send_test_notification() -> dict:
    cfg = _load_config()
    token = cfg.get("bot_token", "")
    chat_id = cfg.get("chat_id", "")

    if not token or not chat_id:
        raise HTTPException(
            status_code=422,
            detail="Telegram credentials not configured. Save bot_token and chat_id first.",
        )

    notifier = TelegramNotifier(token, chat_id)
    ok = notifier.send_message("✅ *Test message from Financial Analysis App* — Telegram notifications are working!")

    if not ok:
        raise HTTPException(status_code=502, detail="Failed to send Telegram message. Check your bot token and chat ID.")

    return {"status": "sent"}
