print("=== BOT STARTING ===")

import os
from telegram.ext import Updater, CommandHandler

TOKEN = os.getenv("transcription_arabic")

def start(update, context):
    update.message.reply_text("Бот запущен ✅")

def main():
    print("=== MAIN CALLED ===")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if _name_ == "_main_":
    main()# -- coding: utf-8 --
"""
Telegram bot: Arabic transliteration + Tajweed rules
Python 3.8+
Railway compatible
Token from env: transcription_arabic
"""

import os
import re
import logging
from typing import List, Tuple

from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# ──────────────────────────────────────────────
# Optional translator
# ──────────────────────────────────────────────
try:
    from googletrans import Translator
    translator = Translator()
    HAS_TRANSLATOR = True
except Exception:
    translator = None
    HAS_TRANSLATOR = False

# ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(_name_)

# ──────────────────────────────────────────────
# Transliteration table
# ──────────────────────────────────────────────
TRANS = {
    'ا': 'a', 'أ': "ʼa", 'إ': "ʼi", 'آ': 'ā',
    'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
    'ح': 'ḥ', 'خ': 'kh', 'د': 'd', 'ذ': 'dh',
    'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
    'ص': 'ṣ', 'ض': 'ḍ', 'ط': 'ṭ', 'ظ': 'ẓ',
    'ع': 'ʿ', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
    'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
    'ه': 'h', 'و': 'w', 'ي': 'y',
    'ء': "ʼ", 'ئ': "ʼ", 'ؤ': "ʼ",
    'ى': 'ā', 'ة': 'h',
    'َ': 'a', 'ِ': 'i', 'ُ': 'u',
    'ً': 'an', 'ٍ': 'in', 'ٌ': 'un',
    'ْ': '', 'ّ': ''
}

DIACRITICS = set(['َ','ِ','ُ','ً','ٍ','ٌ','ْ','ّ'])

# ──────────────────────────────────────────────
# Tajweed rule sets (simplified)
# ──────────────────────────────────────────────
IDGHAM_GHUNNAH = set("ينمو")
IDGHAM_NO_GHUNNAH = set("لر")
IQLAB = {'ب'}
IZHAR = set("ءهعحغخ")
IKHFA = set("تثجذزسشصضطظفقبكل")
QALQALAH = set("قطبجد")

# ──────────────────────────────────────────────
def clean_text(text: str) -> str:
    return text.replace('\u0640', '').strip()

def transliterate(text: str) -> str:
    return ''.join(TRANS.get(ch, ch) for ch in text)

def tajweed_analyze(text: str) -> List[Tuple[int, str, str]]:
    rules = []
    text = clean_text(text)

    for i, ch in enumerate(text):

        if ch == 'ّ':
            rules.append((i, "Shaddah", "Удвоение согласной"))

        if ch == 'ن' or ch in ('ً','ٍ','ٌ'):
            j = i + 1
            while j < len(text) and text[j] in DIACRITICS:
                j += 1
            next_ch = text[j] if j < len(text) else ''

            if next_ch in IDGHAM_GHUNNAH:
                rules.append((i, "Idgham + Ghunnah", "Идгам с гунной"))
            elif next_ch in IDGHAM_NO_GHUNNAH:
                rules.append((i, "Idgham", "Идгам без гунны"))
            elif next_ch in IQLAB:
                rules.append((i, "Iqlab", "Икляб (ن → م)"))
            elif next_ch in IZHAR:
                rules.append((i, "Izhar", "Ясное произношение"))
            elif next_ch in IKHFA:
                rules.append((i, "Ikhfa", "Скрытие с гунной"))

        if ch in QALQALAH:
            rules.append((i, "Qalqalah", "Отскок звука"))

    return rules

def analyze_and_format(text: str) -> str:
    t = clean_text(text)

    output = [
        "📖 Исходный текст:",
        t,
        "",
        "🔤 Транслитерация:",
        transliterate(t),
        "",
        "📘 Таджвид (упрощённо):"
    ]

    rules = tajweed_analyze(t)
    if rules:
        for pos, rule, note in rules:
            frag = t[max(0, pos-3):pos+3]
            output.append(f"- {rule}: {note} ( «{frag}» )")
    else:
        output.append("— правила не найдены")

    if HAS_TRANSLATOR:
        try:
            tr = translator.translate(t, dest='ru')
            output.extend(["", "🌍 Перевод:", tr.text])
        except Exception:
            pass

    return "\n".join(output)

# ──────────────────────────────────────────────
# Telegram handlers
# ──────────────────────────────────────────────
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Ассаляму алейкум!\n"
        "Отправьте арабский текст — я сделаю транслитерацию и таджвид."
    )

def transliterate_cmd(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Использование: /transliterate <арабский текст>")
        return
    text = " ".join(context.args)
    update.message.reply_text(analyze_and_format(text))

def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if re.search(r'[\u0600-\u06FF]', text):
        update.message.reply_text(analyze_and_format(text))
    else:
        update.message.reply_text("Пожалуйста, отправьте арабский текст.")

# ──────────────────────────────────────────────
def main():
    token = os.getenv("transcription_arabic")

    if not token:
        logger.error("❌ ENV transcription_arabic not set")
        return

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("transliterate", transliterate_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    logger.info("✅ Bot started")
    updater.start_polling()
    updater.idle()

# ──────────────────────────────────────────────
if _name_ == "_main_":
    main()
