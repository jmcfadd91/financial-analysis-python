#!/bin/bash
# Prints crontab entries for daily (9am weekdays) and hourly reports.
# Usage: bash scripts/setup_cron.sh
# Then copy the lines into: crontab -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "# Daily at 9am Mon–Fri:"
echo "0 9 * * 1-5 cd $SCRIPT_DIR && /usr/bin/python3 scripts/send_report.py >> logs/report.log 2>&1"
echo ""
echo "# Hourly (market hours 9am–4pm Mon–Fri):"
echo "0 9-16 * * 1-5 cd $SCRIPT_DIR && /usr/bin/python3 scripts/send_report.py >> logs/report.log 2>&1"
