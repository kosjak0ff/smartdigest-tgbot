# SmartDigest Telegram Bot

Headless Python service for Ubuntu VPS that:
- reads new posts from public Telegram channel web pages `https://t.me/s/<channel>`;
- forwards unseen posts to a target Telegram chat or topic;
- stores posts and delivery state in SQLite;
- generates scheduled or manual digests through the Perplexity API;
- sends digests back to Telegram with source links.

## English

### Stack

Python 3.12, `python-telegram-bot`, `httpx`, `BeautifulSoup4`, `SQLite`, `APScheduler`, Perplexity API, `systemd`.

### Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
cp channels.yaml.example channels.yaml
python -m smartdigest_bot
```

### Notes

- On first run the default mode is `mark_seen`, so old channel history is not forwarded.
- Manual digest command: `/digest_now`
- Owner-only commands can be restricted with `TELEGRAM_OWNER_USER_ID`.
- Secret scan:

```bash
detect-secrets scan
```

### systemd

Unit file: [deploy/smartdigest-bot.service](/home/code/codex-projects/smartdigest-tgbot/deploy/smartdigest-bot.service)

### VPS deploy from scratch

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv
sudo useradd -m -s /bin/bash smartdigest || true
sudo -u smartdigest -H bash -lc '
cd /home/smartdigest
git clone https://github.com/kosjak0ff/smartdigest-tgbot.git
cd smartdigest-tgbot
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
cp .env.example .env
cp channels.yaml.example channels.yaml
mkdir -p data
'
sudo -u smartdigest -H nano /home/smartdigest/smartdigest-tgbot/.env
sudo -u smartdigest -H nano /home/smartdigest/smartdigest-tgbot/channels.yaml
sudo cp /home/smartdigest/smartdigest-tgbot/deploy/smartdigest-bot.service /etc/systemd/system/smartdigest-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now smartdigest-bot.service
sudo journalctl -u smartdigest-bot.service -f
```

## Русский

### Что делает

Сервис без веб-интерфейса для Ubuntu VPS:
- читает новые посты из публичных Telegram-каналов через `https://t.me/s/<channel>`;
- пересылает новые посты в указанный чат или topic;
- хранит посты и состояние отправки в SQLite;
- делает дайджесты по расписанию или по команде `/digest_now`;
- отправляет дайджест обратно в Telegram со ссылками на оригиналы.

### Быстрый старт

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
cp channels.yaml.example channels.yaml
python -m smartdigest_bot
```

### Важные замечания

- Безопасный первый запуск включён по умолчанию: `FIRST_RUN_MODE=mark_seen`.
- Команды бота можно ограничить владельцем через `TELEGRAM_OWNER_USER_ID`.
- Для локальной проверки секретов:

```bash
detect-secrets scan
```

### Деплой на VPS с нуля

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv
sudo useradd -m -s /bin/bash smartdigest || true
sudo -u smartdigest -H bash -lc '
cd /home/smartdigest
git clone https://github.com/kosjak0ff/smartdigest-tgbot.git
cd smartdigest-tgbot
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
cp .env.example .env
cp channels.yaml.example channels.yaml
mkdir -p data
'
sudo -u smartdigest -H nano /home/smartdigest/smartdigest-tgbot/.env
sudo -u smartdigest -H nano /home/smartdigest/smartdigest-tgbot/channels.yaml
sudo cp /home/smartdigest/smartdigest-tgbot/deploy/smartdigest-bot.service /etc/systemd/system/smartdigest-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now smartdigest-bot.service
sudo journalctl -u smartdigest-bot.service -f
```
