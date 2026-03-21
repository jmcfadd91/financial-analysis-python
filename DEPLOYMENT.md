# VPS Deployment Guide

Step-by-step instructions for deploying the Financial Analysis app on a VPS, including the FastAPI backend, React frontend, Telegram report cron job, and nginx reverse proxy.

---

## Prerequisites

```bash
# Install Docker + Compose plugin
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # add your user to the docker group
newgrp docker                    # apply without logout
```

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/jmcfadd91/financial-analysis-python.git ~/financial-analysis-python
cd ~/financial-analysis-python
```

If the repo already exists on the VPS:

```bash
cd ~/financial-analysis-python
git fetch origin && git checkout main && git pull origin main
```

---

## Step 2 — Create `.env`

```bash
cp .env.example .env
nano .env
```

Fill in your Telegram credentials (get the token from `@BotFather`; get your chat ID from `api.telegram.org/bot<TOKEN>/getUpdates` after sending `/start` to your bot):

```bash
TELEGRAM_BOT_TOKEN=123456:ABCdef...
TELEGRAM_CHAT_ID=987654321
```

`.env` is gitignored — it stays on the VPS only.

---

## Step 3 — Create runtime directories

```bash
mkdir -p ~/financial-analysis-python/data
mkdir -p ~/financial-analysis-python/logs
```

---

## Step 4 — Build and start with Docker Compose

```bash
cd ~/financial-analysis-python
docker compose up --build -d
```

This starts:
- **API** — FastAPI + uvicorn on port `8000`
- **Frontend** — Vite dev server on port `5173`

Check status:

```bash
docker compose ps
docker compose logs -f        # all logs
docker compose logs api       # API only
```

Verify the API is up:

```bash
curl http://localhost:8000/
# → {"status":"ok","docs":"/docs"}
```

---

## Step 5 — nginx reverse proxy (recommended)

Serves everything on port 80 via a single entry point.

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/financial
```

Paste:

```nginx
server {
    listen 80;
    server_name your-vps-ip-or-domain;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # FastAPI docs
    location /docs {
        proxy_pass http://localhost:8000;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/financial /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## Step 6 — Telegram cron report

`scripts/send_report.py` runs outside Docker and reads `data/` directly from the host. You need a host Python environment with the app's dependencies.

### 6a — Install TA-Lib system library

```bash
sudo apt-get install -y build-essential wget
wget https://github.com/TA-Lib/ta-lib/releases/download/v0.4.0/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib && ./configure --prefix=/usr && sudo make install && cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
```

### 6b — Create host virtualenv

```bash
cd ~/financial-analysis-python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify:

```bash
python3 -c "import talib; print('TA-Lib OK')"
```

### 6c — Test the report script manually

```bash
source .venv/bin/activate
python scripts/send_report.py
# → Telegram message should arrive
```

### 6d — Add the cron job

```bash
# Print correctly-pathed crontab lines for this machine
bash scripts/setup_cron.sh

# Open crontab editor
crontab -e
```

Add this line (daily at 9am Mon–Fri):

```
0 9 * * 1-5 cd /home/<your-user>/financial-analysis-python && .venv/bin/python scripts/send_report.py >> logs/report.log 2>&1
```

Or hourly during market hours (9am–4pm Mon–Fri):

```
0 9-16 * * 1-5 cd /home/<your-user>/financial-analysis-python && .venv/bin/python scripts/send_report.py >> logs/report.log 2>&1
```

---

## Step 7 — Auto-start on reboot

```bash
sudo nano /etc/systemd/system/financial-app.service
```

```ini
[Unit]
Description=Financial Analysis App
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/<your-user>/financial-analysis-python
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable financial-app
sudo systemctl start financial-app
```

---

## Step 8 — Configure Telegram via the UI

1. Open `http://your-vps-ip` in a browser
2. Go to the **Alerts** tab
3. Paste your bot token and chat ID → **Save**
4. Click **Send Test** — a message should arrive in Telegram

---

## Verification checklist

```bash
# App health
curl http://localhost:8000/

# Telegram config endpoint
curl http://localhost:8000/api/notifications/config

# Trigger a report manually
source .venv/bin/activate && python scripts/send_report.py

# Watch cron log
tail -f ~/financial-analysis-python/logs/report.log
```

---

## Updating the app

```bash
cd ~/financial-analysis-python
git pull origin main
docker compose up --build -d
```

---

## Notes

- `data/` is mounted into the Docker container via `volumes: - .:/app`, so `data/watchlist.json` and `data/portfolio.json` written by the app are immediately visible to the host cron script — no sync needed.
- The bot token is stored server-side in `data/notification_config.json` (gitignored via the `data/` pattern) and is masked in all API responses.
- TA-Lib requires the native C library; see Step 6a. The Docker image builds it automatically from source.
