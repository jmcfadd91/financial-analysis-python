#!/usr/bin/env python3
"""Cron entry point: python scripts/send_report.py"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root on path

from dotenv import load_dotenv

load_dotenv()

from src.reporting.notifier import TelegramNotifier

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not token or not chat_id:
    print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
    sys.exit(1)

notifier = TelegramNotifier(token, chat_id)
success = notifier.send_report()
sys.exit(0 if success else 1)
