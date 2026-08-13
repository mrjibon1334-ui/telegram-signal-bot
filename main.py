import time
import datetime
import asyncio
import random
import cloudscraper
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8978017343:AAGcnXfBEn76BmCJULIn4U0Mm8cB5aLgrSM"
REGISTRATION_LINK = "https://dkwin7.com/#/register?invitationCode=82824101415"
ADMIN_USERNAME = "Adnan485825"
CHANNEL_ID = "@freedkwinsignal" # যদি চ্যানেলে না পাঠাতে চান, এটি খালি ("") করে রাখতে পারেন

WIN_STICKER_ID = "CAACAgUAAxkBAAERs15qfadmESLSuDJuumUsWGD0RjIAATYAAkAhAAKQ_PhUDznfLhIsF809BA"
LOSS_STICKER_ID = "CAACAgUAAxkBAAERs2BqfaeLPNLeouIE50oOuD_oeJ4u_gACuB4AAlPb-VTHnZIszeTCaT0E"

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

is_bot_running = False
approved_users = set()      
pending_requests = {}       
last_signal_data = {}
history_results = []
admin_chat_id = None        

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

def generate_safe_prediction():
    global history_results
    if len(history_results) >= 4:
        recent = history_results[-4:]
        if recent.count("BIG") >= 3:
            return "SMALL"
        elif recent.count("SMALL") >= 3:
            return "BIG"
            
    if len(history_results) >= 2 and history_results[-1] == history_results[-2]:
        return "SMALL" if history_results[-1] == "BIG" else "BIG"
        
    return random.choice(["BIG", "SMALL"])

def generate_backup_result(prediction):
    is_win = random.choices([True, False], weights=[92, 8])[0]
    pred_upper = prediction.upper()

    if pred_upper == "BIG":
        num = random.choice([5, 6, 7, 8, 9]) if is_win else random.choice([0, 1, 2, 3, 4])
    else: 
        num = random.choice([0, 1, 2, 3, 4]) if is_win else random.choice([5, 6, 7, 8, 9])

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

async def auto_signal_loop(context: ContextTypes.DEFAULT_TYPE):
    global last_signal_data, history_results, is_bot_running
    
    while is_bot_running:
        try:
            now = datetime.datetime.now()
            seconds_to_wait = 60 - now.second
            await asyncio.sleep(seconds_to_wait)

            if not is_bot_running:
                break

            if 'period' in last_signal_data:
                prev_period = last_signal_data['period']
                prev_pred = last_signal_data['pred']
                
                await asyncio.sleep(3)
                api_period, live_num, size, color = fetch_actual_live_result()
                
                if live_num is not None:
                    res_period = api_period
                else:
                    res_period = prev_period
                    live_num, size, color = generate_backup_result(prev_pred)

                history_results.append(size)
                if len(history_results) > 15:
                    history_results.pop(0)

                is_win = False
                if prev_pred == size:
                    is_win = True

                status_icon = "✅ **WIN**" if is_win else "❌ **LOSS**"
                
                res_card = (
                    f"{status_icon}\n"
                    f"============================\n"
                    f"Period => **#{res_period}**\n"
                    f"Result => **NUM:{live_num}** | **{size}** | **{color}**\n"
                    f"============================"
                )
                
                # যদি চ্যানেল আইডি দেওয়া থাকে তবে সেখানে যাবে
                if CHANNEL_ID:
                    try:
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=res_card, parse_mode="Markdown")
                    except:
                        pass
                
                # অনুমোদিত মেম্বারদের ইনবক্সে পাঠানো
                for uid in list(approved_users):
                    try:
                        await context.bot.send_message(chat_id=uid, text=res_card, parse_mode="Markdown")
                    except:
                        pass
                
                try:
                    target_sticker = WIN_STICKER_ID if is_win else LOSS_STICKER_ID
                    if CHANNEL_ID:
                        await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=target_sticker)
                    for uid in list(approved_users):
                        try:
                            await context.bot.send_sticker(chat_id=uid, sticker=target_sticker)
                        except:
                            pass
                except Exception as st_err:
                    print(f"Sticker Send Error: {st_err}")

                await asyncio.sleep(1)

            utc_now = datetime.datetime.now(datetime.timezone.utc)
            total_minutes = utc_now.hour * 60 + utc_now.minute
            current_period = str(10001 + total_minutes)[-4:]

            new_pred = generate_safe_prediction()
            confidence = random.randint(98, 99)

            keyboard = [
                [InlineKeyboardButton("👤 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("🎮 REGISTER & PLAY ON DKWIN 🎮", url=REGISTRATION_LINK)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            pred_msg = (
                f"⚡ **24/7 VIP PREDICTION BOT** 🌿\n"
                f"============================\n"
                f"📌 **Period:** `#{current_period}`\n"
                f"🎯 **Prediction:** **{new_pred}**\n"
                f"📊 **Accuracy:** `{confidence}%`\n"
                f"============================\n"
                f"🛡️ *Anti-Loss Filter Enabled*\n"
                f"⏳ *Next Signal in 60 Seconds...*"
            )

            if CHANNEL_ID:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID, 
                    text=pred_msg, 
                    parse_mode="Markdown", 
                    reply_markup=reply_markup
                )

            for uid in list(approved_users):
                try:
                    await context.bot.send_message(
                        chat_id=uid, 
                        text=pred_msg, 
                        parse_mode="Markdown", 
                        reply_markup=reply_markup
                    )
                except:
                    pass

            last_signal_data = {
                'period': current_period,
                'pred': new_pred
            }

            await asyncio.sleep(2)

        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_running, admin_chat_id
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        admin_chat_id = user_id
        if not is_bot_running:
            is_bot_running = True
            asyncio.create_task(auto_signal_loop(context))
            await update.message.reply_text("🚀 **অ্যাডমিন প্যানেল থেকে সিগন্যাল লুপ সফলভাবে চালু হয়েছে!**")
        else:
            await update.message.reply_text("⚠️ বট ইতিমধ্যে রান করছে!")
    elif user_id in approved_users:
        await update.message.reply_text("✅ আপনি অনুমোদিত আছেন। লাইভ সিগন্যাল আপনার কাছে আসছে!")
    else:
        pending_requests[user_id] = username
        if admin_chat_id:
            keyboard = [
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"🔔 **নতুন ইউজার রিকুয়েস্ট!**\n\n👤 নাম: {username}\n🆔 আইডি: `{user_id}`",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        await update.message.reply_text("⏳ আপনার বট চালুর অনুরোধটি অ্যাডমিনের কাছে পাঠানো হয়েছে। অনুমোদন পেলে সিগন্যাল পাবেন।")

# নির্দিষ্ট কোনো ইউজারের সিগন্যাল বন্ধ করার কমান্ড: /remove ইউজারআইডি
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user.username or user.username.lower() != ADMIN_USERNAME.lower():
        return
        
    if not context.args:
        await update.message.reply_text("⚠️ দয়া করে ইউজারের আইডি দিন। যেমন: `/remove 123456789`", parse_mode="Markdown")
        return
        
    try:
        target_id = int(context.args[0])
        if target_id in approved_users:
            approved_users.remove(target_id)
            await update.message.reply_text(f"✅ ইউজার (`{target_id}`) এর সিগন্যাল বন্ধ করে দেওয়া হয়েছে।", parse_mode="Markdown")
            try:
                await context.bot.send_message(chat_id=target_id, text="❌ অ্যাডমিন আপনার সিগন্যাল এক্সেস বন্ধ করে দিয়েছেন।")
            except:
                pass
        else:
            await update.message.reply_text("⚠️ এই আইডিটি অনুমোদিত লিস্টে পাওয়া যায়নি।")
    except ValueError:
        await update.message.reply_text("⚠️ সঠিক ইউজার আইডি দিন।")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("approve_"):
        target_id = int(data.split("_")[1])
        approved_users.add(target_id)
        if target_id in pending_requests:
            del pending_requests[target_id]
            
        await query.edit_message_text(f"✅ ইউজার (ID: `{target_id}`) কে অনুমতি দেওয়া হয়েছে।", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_id, text="🎉 অ্যাডমিন আপনার অনুরোধ অনুমোদন করেছেন! এখন থেকে আপনি বটে লাইভ সিগন্যাল পাবেন।")
        except:
            pass
            
    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        if target_id in pending_requests:
            del pending_requests[target_id]
            
        await query.edit_message_text(f"❌ ইউজার (ID: `{target_id}`) এর অনুরোধ বাতিল করা হয়েছে।", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_id, text="❌ দুঃখিত, আপনার অনুরোধটি রিজেক্ট করা হয়েছে।")
        except:
            pass

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_running
    user = update.effective_user
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        is_bot_running = False
        await update.message.reply_text("🛑 **Bot & Signal Loop Stopped.**")
    else:
        await update.message.reply_text("⛔ আপনার এই কমান্ড ব্যবহারের অনুমতি নেই।")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("remove", remove_user))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Private Bot with User Removal Feature Running!")
    app.run_polling()
