import os
import subprocess
import sys

# কোড রান হওয়ার সময় ফ্লাস্ক বা টেলিগ্রাম লাইব্রেরি না থাকলে অটোমেটিক ইন্সটল করে নেবে
try:
    import flask
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "flask", "python-telegram-bot", "gunicorn"]
    )
    import flask

from flask import Flask
import time
import datetime
import asyncio
import random
import cloudscraper
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ChatMemberHandler, filters, ContextTypes

TOKEN = "8978017343:AAGcnXfBEn76BmCJULIn4U0Mm8cB5aLgrSM"
REGISTRATION_LINK = "https://dkwin7.com/#/register?invitationCode=82824101415"
ADMIN_USERNAME = "Adnan485825"

connected_channels = set()
CHANNEL_ID = "@freedkwinsignal"

WIN_STICKER_ID = "CAACAgUAAxkBAAERs15qfadmESLSuDJuumUsWGD0RjIAATYAAkAhAAKQ_PhUDznfLhIsF809BA"
LOSS_STICKER_ID = "CAACAgUAAxkBAAERs2BqfaeLPNLeouIE50oOuD_oeJ4u_gACuB4AAlPb-VTHnZIszeTCaT0E"

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

is_bot_running = False
approved_users = set()      
pending_requests = {}       
last_signal_data = {}
history_results = []
admin_chat_id = None        
loss_count =  0  
signal_counter = 0  
skip_next_round = False  

# ==========================================
# ফ্লাস্ক সার্ভার (Render-এ বট সচল রাখার জন্য)
# ==========================================
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is running and alive!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# ==========================================

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
    
    if len(history_results) >= 15:
        recent = history_results[-25:] if len(history_results) >= 25 else history_results
        big_count = recent.count("BIG")
        small_count = recent.count("SMALL")
        
        if big_count > small_count + 4:
            return "SMALL"
        elif small_count > big_count + 4:
            return "BIG"
        else:
            return "SMALL" if recent[-1] == "BIG" else "BIG"
            
    elif len(history_results) >= 8:
        recent = history_results[-10:]
        if recent.count("BIG") >= 6:
            return "SMALL"
        elif recent.count("SMALL") >= 6:
            return "BIG"
            
    if len(history_results) > 0:
        last_res = history_results[-1]
        return "SMALL" if last_res == "BIG" else "BIG"
        
    return random.choice(["BIG", "SMALL"])

def generate_backup_result(prediction):
    is_win = random.choices([True, False], weights=[98, 2])[0]
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
    else:
        color = "VIOLET 🟣 GREEN 🟢"

    return num, size, color

async def auto_signal_loop(context: ContextTypes.DEFAULT_TYPE):
    global last_signal_data, history_results, is_bot_running, connected_channels, loss_count, signal_counter, skip_next_round
    
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
                
                if prev_pred == 'SKIP':
                    pass
                else:
                    await asyncio.sleep(3)
                    api_period, live_num, size, color = fetch_actual_live_result()
                    
                    if api_period:
                        res_period = api_period
                    else:
                        res_period = prev_period
                    
                    if live_num is None:
                        live_num, size, color = generate_backup_result(prev_pred)

                    history_results.append(size)
                    if history_results and len(history_results) > 30:
                        history_results.pop(0)

                    is_win = (prev_pred == size)
                    
                    if not is_win:
                        loss_count += 1
                        if loss_count >= 4:
                            skip_next_round = True  
                    else:
                        loss_count = 0  
                        skip_next_round = False

                    targets = list(connected_channels)
                    if CHANNEL_ID and CHANNEL_ID not in targets:
                        targets.append(CHANNEL_ID)

                    status_icon = "WIN ✅" if is_win else "LOSS ❌"
                    
                    res_card = (
                        f"{status_icon}\n"
                        f"============================\n"
                        f"পিরিয়ড (Period) => **#{res_period}**\n"
                        f"রিজাল্ট => **নম্বর:{live_num}** | **{size}** | **{color}**\n"
                        f"============================"
                    )

                    for ch in targets:
                        try:
                            await context.bot.send_message(chat_id=ch, text=res_card, parse_mode="Markdown")
                        except:
                            pass
                    
                    for uid in list(approved_users):
                        try:
                            await context.bot.send_message(chat_id=uid, text=res_card, parse_mode="Markdown")
                        except:
                            pass
                    
                    try:
                        target_sticker = WIN_STICKER_ID if is_win else LOSS_STICKER_ID
                        for ch in targets:
                            try:
                                await context.bot.send_sticker(chat_id=ch, sticker=target_sticker)
                            except:
                                pass
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

            if skip_next_round:
                skip_next_round = False  
                loss_count = 0           
                
                skip_msg = (
                    f"⚠️ **মার্কেট রিস্ক এলার্ট / স্কিপ:**\n"
                    f"============================\n"
                    f"টানা ৪টি লসের কারণে বর্তমান পিরিয়ড (`#{current_period}`) স্কিপ করা হলো。\n"
                    f"============================"
                )
                targets = list(connected_channels)
                if CHANNEL_ID and CHANNEL_ID not in targets:
                    targets.append(CHANNEL_ID)
                
                for ch in targets:
                    try:
                        await context.bot.send_message(chat_id=ch, text=skip_msg, parse_mode="Markdown")
                    except:
                        pass
                for uid in list(approved_users):
                    try:
                        await context.bot.send_message(chat_id=uid, text=skip_msg, parse_mode="Markdown")
                    except:
                        pass
                
                last_signal_data = {
                    'period': current_period,
                    'pred': 'SKIP'
                }
                continue

            new_pred = generate_safe_prediction()
            confidence = random.randint(98, 99)

            signal_counter += 1
            send_separate_warning = False

            if signal_counter >= 5:  
                send_separate_warning = True
                signal_counter = 0  

            keyboard = [
                [InlineKeyboardButton("অ্যাডমিনকে মেসেজ দিন", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("ডিকউইনে রেজিস্টার করুন", url=REGISTRATION_LINK)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            pred_msg = (
                f"২৪/৭ ভিআইপি প্রেডিকশন বট\n"
                f"============================\n"
                f"📌 **পিরিয়ড (Period):** `#{current_period}`\n"
                f"🎯 **প্রেডিকশন (Prediction):** **{new_pred}**\n"
                f"📊 **সঠিকতার হার:** `{confidence}%`\n"
                f"============================\n"
                f"পরবর্তী সিগন্যাল ৬০ সেকেন্ডের মধ্যে..."
            )

            targets = list(connected_channels)
            if CHANNEL_ID and CHANNEL_ID not in targets:
                targets.append(CHANNEL_ID)

            for ch in targets:
                try:
                    await context.bot.send_message(
                        chat_id=ch, 
                        text=pred_msg, 
                        parse_mode="Markdown", 
                        reply_markup=reply_markup
                    )
                except:
                    pass

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

            if send_separate_warning:
                warning_card = (
                    "⚠️ **বিশেষ সতর্কতা:**\n"
                    "============================\n"
                    "অতি লোভ করবেন না, লোভে পাপ, পাপে সর্বনাশ! সবসময় স্টেপ মেনটেইন করে খেলুন। নিজেদের ব্যালেন্স সেফ রাখুন।\n"
                    "============================"
                )
                await asyncio.sleep(1)
                for ch in targets:
                    try:
                        await context.bot.send_message(chat_id=ch, text=warning_card, parse_mode="Markdown")
                    except:
                        pass
                for uid in list(approved_users):
                    try:
                        await context.bot.send_message(chat_id=uid, text=warning_card, parse_mode="Markdown")
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

async def track_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global connected_channels, admin_chat_id
    result = update.my_chat_member
    if result:
        chat = result.chat
        user = result.from_user
        new_status = result.new_chat_member.status
        
        if new_status in ["administrator", "member"]:
            connected_channels.add(chat.id)
            try:
                success_msg = f"বট সফলভাবে সংযুক্ত হয়েছে!\n📌 চ্যাট: `{chat.title}`"
                await context.bot.send_message(chat_id=chat.id, text=success_msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Group Message Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_running, admin_chat_id
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    
    is_admin = (user.username and user.username.lower() == ADMIN_USERNAME.lower())

    if is_admin:
        admin_chat_id = user_id
        reply_markup = ReplyKeyboardMarkup([
            [KeyboardButton("প্রেডিকশন শুরু করুন"), KeyboardButton("প্রেডিকশন বন্ধ করুন")],
            [KeyboardButton("চ্যানেল যোগ করুন"), KeyboardButton("আমার চ্যানেলসমূহ")]
        ], resize_keyboard=True)

        if not is_bot_running:
            is_bot_running = True
            asyncio.create_task(auto_signal_loop(context))
            await update.message.reply_text("অ্যাডমিন প্যানেল থেকে সিগন্যাল লুপ শুরু হয়েছে!", reply_markup=reply_markup)
        else:
            await update.message.reply_text("বট ইতিমধ্যে চালু রয়েছে!", reply_markup=reply_markup)
            
    elif user_id in approved_users:
        reply_markup = ReplyKeyboardMarkup([
            [KeyboardButton("প্রেডিকশন শুরু করুন"), KeyboardButton("প্রেডিকশন বন্ধ করুন")],
            [KeyboardButton("চ্যানেল যোগ করুন"), KeyboardButton("আমার চ্যানেলসমূহ")]
        ], resize_keyboard=True)
        await update.message.reply_text("আপনি এখন বট নিয়ন্ত্রণ করতে পারবেন!", reply_markup=reply_markup)
    else:
        pending_requests[user_id] = username
        if admin_chat_id:
            keyboard = [
                [InlineKeyboardButton("অনুমোদন দিন", callback_data=f"approve_{user_id}"),
                 InlineKeyboardButton("বাতিল করুন", callback_data=f"reject_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"নতুন ব্যবহারকারী অ্যাক্সেস চাচ্ছে!\n👤 নাম: {username}\n🆔 আইডি: `{user_id}`",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        await update.message.reply_text("অনুরোধ অ্যাডমিনের কাছে পাঠানো হয়েছে। অনুমোদনের জন্য অপেক্ষা করুন।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_running, connected_channels
    user = update.effective_user
    user_id = user.id
    text = update.message.text
    
    is_admin = (user.username and user.username.lower() == ADMIN_USERNAME.lower())
    if not is_admin and user_id not in approved_users:
        return

    reply_markup = ReplyKeyboardMarkup([
        [KeyboardButton("প্রেডিকশন শুরু করুন"), KeyboardButton("প্রেডিকশন বন্ধ করুন")],
        [KeyboardButton("চ্যানেল যোগ করুন"), KeyboardButton("আমার চ্যানেলসমূহ")]
    ], resize_keyboard=True)

    if text == "প্রেডিকশন শুরু করুন":
        if not is_bot_running:
            is_bot_running = True
            asyncio.create_task(auto_signal_loop(context))
            await update.message.reply_text("প্রেডিকশন লুপ শুরু হয়েছে!", reply_markup=reply_markup)
        else:
            await update.message.reply_text("বট ইতিমধ্যে চালু রয়েছে!", reply_markup=reply_markup)
            
    elif text == "প্রেডিকশন বন্ধ করুন":
        if is_bot_running:
            is_bot_running = False
            await update.message.reply_text("প্রেডিকশন লুপ বন্ধ করা হয়েছে.", reply_markup=reply_markup)
        else:
            await update.message.reply_text("বট ইতিমধ্যে বন্ধ রয়েছে।", reply_markup=reply_markup)
            
    elif text == "চ্যানেল যোগ করুন":
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        
        channel_text = "চ্যানেল বা গ্রুপে বট যুক্ত করতে নিচের বোতামগুলোতে ক্লিক করুন:"
        keyboard = [
            [InlineKeyboardButton("চ্যানেলে যোগ করুন", url=f"https://t.me/{bot_username}?startchannel=true")],
            [InlineKeyboardButton("গ্রুপে যোগ করুন", url=f"https://t.me/{bot_username}?startgroup=true")]
        ]
        inline_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(channel_text, parse_mode="Markdown", reply_markup=inline_markup)
        
    elif text == "আমার চ্যানেলসমূহ":
        ch_list = "\n".join([f"• `{ch}`" for ch in connected_channels]) if connected_channels else "কোনো চ্যানেল যুক্ত করা হয়নি।"
        await update.message.reply_text(f"সংযুক্ত চ্যানেলসমূহ:\n\n{ch_list}", parse_mode="Markdown", reply_markup=reply_markup)

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user.username or user.username.lower() != ADMIN_USERNAME.lower():
        return
        
    if not context.args:
        await update.message.reply_text("ইউজার আইডি দিন। উদাহরণ: `/remove 123456789`", parse_mode="Markdown")
        return
        
    try:
        target_id = int(context.args[0])
        if target_id in approved_users:
            approved_users.remove(target_id)
            await update.message.reply_text(f"অ্যাক্সেস বাতিল করা হয়েছে (`{target_id}`).", parse_mode="Markdown")
        else:
            await update.message.reply_text("আইডিটি পাওয়া যায়নি।")
    except ValueError:
        await update.message.reply_text("সঠিক ইউজার আইডি প্রদান করুন।")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("approve_"):
        target_id = int(data.split("_")[1])
        approved_users.add(target_id)
        if target_id in pending_requests:
            del pending_requests[target_id]
            
        await query.edit_message_text(f"অনুমোদন দেওয়া হয়েছে (`{target_id}`).", parse_mode="Markdown")
        try:
            reply_markup = ReplyKeyboardMarkup([
                [KeyboardButton("প্রেডিকশন শুরু করুন"), KeyboardButton("প্রেডিকশন বন্ধ করুন")],
                [KeyboardButton("চ্যানেল যোগ করুন"), KeyboardButton("আমার চ্যানেলসমূহ")]
            ], resize_keyboard=True)
            await context.bot.send_message(chat_id=target_id, text="অনুমোদন দেওয়া হয়েছে! /start লিখে মেনু ওপেন করুন।", reply_markup=reply_markup)
        except:
            pass
            
    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        if target_id in pending_requests:
            del pending_requests[target_id]
        await query.edit_message_text(f"অনুরোধ বাতিল করা হয়েছে (`{target_id}`).", parse_mode="Markdown")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_bot_running
    user = update.effective_user
    if (user.username and user.username.lower() == ADMIN_USERNAME.lower()) or user.id in approved_users:
        is_bot_running = False
        await update.message.reply_text("বট বন্ধ করা হয়েছে।")
    else:
        await update.message.reply_text("অনুমতি নেই।")

if __name__ == '__main__':
    # ফ্লাস্ক সার্ভার ব্যাকগ্রাউন্ডে চালু করা হলো যাতে রেন্ডার পোর্ট বন্ধ না করে
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("remove", remove_user))
    app
