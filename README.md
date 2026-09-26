# Nicegram refund-check bot

Telegram bot that checks Nicegram export files before a deal (checksums + basic guidance against star/TON scams).

## Run

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="<token>"
python bot.py
```

Commands: `/start`, `/help`, or use the reply keyboard (📘 Инструкция / 🔍 Проверить файл). Send any document to check it.
