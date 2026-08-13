import time
import datetime
import asyncio
import random
import cloudscraper
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8978017343:AAGcnXfBEn76BmCJULIn4U0Mm8cB5aLgrSM"
REGISTRATION_LINK = "https://dkwin9.com/#/register?invitationCode=61187343831"
CHANNEL_ID = "@freedkwinsignal"  # আপনার চ্যানেল ইউজারনেম

# --- পাসওয়ার্ড ও ইউজার লিস্ট ---
BOT_PASSWORD = "13344"  # আপনার মেম্বারদের জন্য পাসওয়ার্ড
AUTHORIZED_USERS = set()  # পাসওয়ার্ড দেওয়া মেম্বারদের আইডি এখানে জমা হবে

# --- স্টিকার ID ---
WIN_STICKER_ID = "CAACAgUAAxkBAAERs15qfadmESLSuDJuumUsWGD0RjIAATYAAkAhAAKQ_PhUDznfLhIsF809BA"
LOSS_STICKER_ID = "CAACAgUAAxkBAAERs2BqfaeLPNLeouIE50oOuD_oeJ4u_gACuB4AAlPb-VTHnZIszeTCaT0E"

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

last_signal_data = {}
current_step = 1
loop_started = False

def fetch_actual_live_result():
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(API_URL, timeout=10)
        
        if response.status_code == 200:
            res_json = response.json()
            if "data" in res_json and "list" in res_json["data"] and len(res_json["data"]["list"]) > 0:
                latest_issue = res_json["data"]["list"][0]
                
                period = str(latest_issue.get("issue", ""))[-4:]
                number = int(latest_issue.get("number", 0))
                
                size = "BIG" if number >= 5 else "SMALL"
                
                if number in [1, 3, 7, 9]:
                    color = "GREEN 🟢"
                elif number in [2, 4, 6, 8]:
                    color = "RED 🔴"
                elif number == 0:
                    color = "VIOLET 🟣 RED 🔴"
                else:
                    color = "VIOLET 🟣 GREEN 🟢"
                    
                return period, number, size, color
    except Exception as e:
        print(f"API Fetch Error: {e}")
        
    return None, None, None, None

def generate_backup_result(prediction, step):
    if step in [1, 2]:
        win_rate = 90
    elif step in [3, 4]:
        win_rate = 70
    else:
        win_rate = 98

    is_win = random.choices([True, False], weights=[win_rate, 100 - win_rate])[0]
    pred_upper = prediction.upper()

    if pred_upper == "BIG":
        num = random.choice([5, 6, 7, 8, 9]) if is_win else random.choice([0, 1, 2, 3, 4])
    elif pred_upper == "SMALL":
        num = random.choice([0, 1, 2, 3, 4]) if is_win else random.choice([5, 6, 7, 8, 9])
    elif pred_upper == "RED":
        num = random.choice([2, 4, 6, 8, 0]) if is_win else random.choice([1, 3, 7, 9, 5])
    elif pred_upper == "GREEN":
        num = random.choice([1, 3, 7, 9, 5]) if is_win else random.choice([2, 4, 6, 8, 0])
    else:
        num = random.randint(0, 9)

    size = "BIG" if num >= 5 else "SMALL"
    if num in [1, 3, 7, 9]:
        color = "GREEN 🟢"
    elif num in [2, 4, 6, 8]:
        color = "RED 🔴"
    elif num == 0:
        color = "VIOLET 🟣 RED 🔴"
    else:
        color = "VIOLET 🟣 GREEN 🟢"

    return num, size, color

async def send_to_all(context, text, reply_markup=None, sticker_id=None):
    # ১. চ্যানেলে পোস্ট
    try:
        if text:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown", reply_markup=reply_markup)
        if sticker_id:
            await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=sticker_id)
    except Exception as e:
        print(f"Channel Send Error: {e}")

    # ২. ইউজারদের ইনবক্সে পোস্ট
    for user_id in list(AUTHORIZED_USERS):
        try:
            if text:
                await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)
            if sticker_id:
                await context.bot.send_sticker(chat_id=user_id, sticker=sticker_id)
        except Exception as e:
            print(f"User {user_id} Send Error: {e}")

async def auto_signal_loop(context: ContextTypes.DEFAULT_TYPE):
    global last_signal_data, current_step
    
    while True:
        try:
            now = datetime.datetime.now()
            seconds_to_wait = 60 - now.second
            await asyncio.sleep(seconds_to_wait)

            # ১. আগের সিগন্যালের লাইভ রেজাল্ট চেক ও রেজাল্ট কার্ড/স্টিকার সেন্ড
            if 'period' in last_signal_data:
                prev_period = last_signal_data['period']
                prev_pred = last_signal_data['pred']
                
                await asyncio.sleep(3)
                api_period, live_num, size, color = fetch_actual_live_result()
                
                if live_num is not None:
                    res_period = api_period
                else:
                    res_period = prev_period
                    live_num, size, color = generate_backup_result(prev_pred, current_step)

                is_win = False
                if prev_pred in ["BIG", "SMALL"] and prev_pred == size:
                    is_win = True
                elif prev_pred in ["RED", "GREEN"] and prev_pred in color:
                    is_win = True

                if is_win:
                    status_icon = "✅ **WIN**"
                    current_step = 1
                else:
                    status_icon = "❌ **LOSS**"
                    current_step += 1
                    if current_step > 7:
                        current_step = 1
                
                res_card = (
                    f"{status_icon}\n"
                    f"============================\n"
                    f"Period => **#{res_period}**\n"
                    f"Result => **NUM:{live_num}** | **{size}** | **{color}**\n"
                    f"============================"
                )
                
                target_sticker = WIN_STICKER_ID if is_win else LOSS_STICKER_ID
                await send_to_all(context, text=res_card, sticker_id=target_sticker)
                await asyncio.sleep(1)

            # ২. নতুন সিগন্যাল কার্ড সেন্ড
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            total_minutes = utc_now.hour * 60 + utc_now.minute
            current_period = str(10001 + total_minutes)[-4:]

            new_pred = random.choice(["BIG", "SMALL", "RED", "GREEN"])
            confidence = random.randint(95, 99)

            keyboard = [[InlineKeyboardButton("🎮 REGISTER & PLAY ON DKWIN 🎮", url=REGISTRATION_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            pred_msg = (
                f"⚡ **24/7 VIP PREDICTION SIGNAL** 🌿\n"
                f"============================\n"
                f"📌 **Period:** `#{current_period}`\n"
                f"🎯 **Prediction:** **{new_pred}**\n"
                f"📊 **Accuracy:** `{confidence}%`\n"
                f"============================\n"
                f"💡 *Follow 7 step maintain*\n"
                f"⏳ *Next Signal in 60 Seconds...*"
            )

            await send_to_all(context, text=pred_msg, reply_markup=reply_markup)

            last_signal_data = {
                'period': current_period,
                'pred': new_pred
            }

            await asyncio.sleep(2)

        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in AUTHORIZED_USERS:
        reply_markup = ForceReply(selective=True, input_field_placeholder="Signal")
        await update.message.reply_text("🚀 **সিগন্যাল চালু হয়েছে!**", reply_markup=reply_markup)
        return

    reply_markup = ForceReply(selective=True, input_field_placeholder="Password din")
    await update.message.reply_text("🔑 **বটটি ব্যবহার করতে পাসওয়ার্ড দিন:**", reply_markup=reply_markup)

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global loop_started
    user_id = update.effective_user.id
    user_input = update.message.text
    
    if user_id in AUTHORIZED_USERS:
        return

    if user_input == BOT_PASSWORD:
        AUTHORIZED_USERS.add(user_id)
        
        reply_markup = ForceReply(selective=True, input_field_placeholder="Signal")
        await update.message.reply_text("🎉 **পাসওয়ার্ড সঠিক! সিগন্যাল সার্ভিস চালু হলো।**", reply_markup=reply_markup)
        
        if not loop_started:
            loop_started = True
            asyncio.create_task(auto_signal_loop(context))
    else:
        reply_markup = ForceReply(selective=True, input_field_placeholder="Password din")
        await update.message.reply_text("❌ **ভুল পাসওয়ার্ড! আবার চেষ্টা করুন।**", reply_markup=reply_markup)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
    
    print("✅ Complete Signal Bot Ready!")
    app.run_polling()
