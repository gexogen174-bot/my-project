"""Nicegram refund-check Telegram bot."""
import hashlib
import logging
import os
import tempfile

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot API file download limit for bots.
MAX_FILE_SIZE = 20 * 1024 * 1024

INSTRUCTION_BUTTON = "📘 Инструкция"
CHECK_BUTTON = "🔍 Проверить файл"


def get_bot_token() -> str:
    """Return bot token from env, failing fast with a clear message."""
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Bot token is not configured. Set TELEGRAM_BOT_TOKEN env var.")
    return token


def format_file_size(num_bytes: int) -> str:
    """Format bytes as human-readable size."""
    if num_bytes < 1024:
        return f"{num_bytes} Б"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} КБ"
    return f"{num_bytes / (1024 * 1024):.1f} МБ"


def calculate_checksums(file_path: str):
    """Hash a file in chunks so large uploads don't exhaust memory."""
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha1.hexdigest(), sha256.hexdigest()


def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(INSTRUCTION_BUTTON)], [KeyboardButton(CHECK_BUTTON)]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Этот бот проверяет файлы Nicegram перед сделкой "
        "и помогает заметить признаки скама.\n\n"
        "Выбери действие 👇",
        reply_markup=main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступные действия:\n"
        f"{INSTRUCTION_BUTTON} — как экспортировать файл из Nicegram\n"
        f"{CHECK_BUTTON} — прислать файл на проверку\n\n"
        "Или просто отправь файл сюда.",
        reply_markup=main_keyboard(),
    )


async def handle_instruction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📘 Инструкция по использованию\n\n"
        "1️⃣ В Nicegram → выбери аккаунт → немного вниз → Экспортировать как файл.\n"
        "2️⃣ Выбери нужный аккаунт и пришли файл сюда.\n"
        "3️⃣ Я проверю структуру и подскажу, если есть признаки скама.\n\n"
        "💡 Бот не делает переводы и не участвует в продаже NFT.\n"
        "Он создан для защиты от мошеннических схем со звёздами и TON."
    )


async def handle_check_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📎 Пришли мне файл для проверки "
        f"(до {format_file_size(MAX_FILE_SIZE)})."
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    if document is None:
        await update.message.reply_text("Не вижу файла. Пришли документ как файл, а не как фото.")
        return
    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            f"Файл слишком большой ({format_file_size(document.file_size)}). "
            f"Пришли файл до {format_file_size(MAX_FILE_SIZE)}."
        )
        return

    status = await update.message.reply_text("⏳ Проверяю файл…")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".nicegram") as tmp:
            tmp_path = tmp.name
        tg_file = await document.get_file()
        await tg_file.download_to_drive(tmp_path)
        size = os.path.getsize(tmp_path)
        if size > MAX_FILE_SIZE:
            await status.edit_text(
                f"Файл слишком большой ({format_file_size(size)}). "
                f"Пришли файл до {format_file_size(MAX_FILE_SIZE)}."
            )
            return
        if size == 0:
            await status.edit_text("Файл пустой (0 Б). Проверь экспорт в Nicegram.")
            return
        md5, sha1, sha256 = calculate_checksums(tmp_path)
    except Exception:
        logger.exception("file check failed")
        await status.edit_text("⚠️ Не получилось проверить файл. Попробуй отправить его ещё раз.")
        return
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    await status.edit_text(
        "🧾 Результат проверки файла:\n"
        f"📄 Имя: {document.file_name or 'без имени'}\n"
        f"📏 Размер: {format_file_size(size)}\n"
        f"📁 Тип: {document.mime_type or 'unknown/unknown'}\n\n"
        "🔐 Контрольные суммы:\n"
        f"MD5: <code>{md5}</code>\n"
        f"SHA1: <code>{sha1}</code>\n"
        f"SHA256: <code>{sha256}</code>\n\n"
        "Результат анализа:\n"
        "✅ Файл прочитан, явных ошибок структуры нет. "
        "Это не гарантия безопасности сделки.\n\n"
        "🛡️ Совет: если покупатель звёзд просил файл «для проверки на рефаунд», "
        "не переводи ничего до завершения сделки.",
        parse_mode="HTML",
    )


async def handle_unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback so free-form text never leaves the user without a reply."""
    await update.message.reply_text(
        "Не понял сообщение. Выбери действие на клавиатуре 👇 или отправь /help.",
        reply_markup=main_keyboard(),
    )


async def handle_non_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Я проверяю только файлы. Пришли документ как файл, а не фото или видео.")


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Regex(f"^{INSTRUCTION_BUTTON}$"), handle_instruction))
    app.add_handler(MessageHandler(filters.Regex(f"^{CHECK_BUTTON}$"), handle_check_request))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.AUDIO, handle_non_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_text))
    return app


def main() -> None:
    app = build_app(get_bot_token())
    app.run_polling()


if __name__ == "__main__":
    main()
