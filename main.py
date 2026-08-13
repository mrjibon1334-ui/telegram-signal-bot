import asyncio
import random
import cloudscraper
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8978017343:AAGcnXfBEn76BmCJULIn4U0Mm8cB5aLgrSM"
REGISTRATION_LINK = "https://dkwin9.com/#/register?invitationCode=61187343831''
CHANNEL_ID = "@freedkwinsignal"

BOT_PASSWORD = "13344"
AUTHORIZED_USERS = set()

WIN_STICKER_ID = "CAACAgUAAxkBAAErs15qfadmESLSuDJuum"
LOSS_STICKER_ID = "CAACAgUAAxkBAAErs2BqfaeLPNLeouIE5"

API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo"

last_signal_data = {}
current_step = 1
loop_started = False

def fetch_actual_live_result():
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(API_URL, timeout=10)
        
        if response.status_code == 200:
            res_json = response.json()
            if "data" in res_json and "list" in res_json["data"]:
                latest_issue = res_json["data"]["list"][0]
                
                period = str(latest_issue.get("issue", ""))
                number = int(latest_issue.get("number", 0))
                
                size = "BIG" if number >= 5 else "SMALL"
                
                if number in [1, 3, 7, 9]:
                    color = "GREEN 🟢"
                elif number in [2, 4, 6, 8]:
                    color = "RED 🔴"
                elif number == 0:
                    color = "RED & PURPLE 🔴🟣"
                elif number == 5:
                    color = "GREEN & PURPLE 🟢🟣"
                else:
                    color = "UNKNOWN"
                    
                return period, number, size, color
    except Exception as e:
        print(f"API Fetch Error: {e}")
    return None, None, None, None

async def auto_signal_loop(context: ContextTypes.DEFAULT_TYPE):
    global last_signal_data, current_step
    
    while True:
        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(API_URL, timeout=10)
            
            if response.status_code == 200:
                res_json = response.json()
                if "data" in res_json and "list" in res_json["data"]:
                    latest_issue = res_json["data"]["list"][0]
                    current_period = str(latest_issue.get("issue", ""))
                    next_period = str(int(current_period) + 1)
                else:
                    await asyncio.sleep(10)
                    continue
            else:
                await asyncio.sleep(10)
                continue

            if last_signal_data:
                old_period = last_signal_data.get("period")
                predicted_size = last_signal_data.get("size")
                
                if old_period == current_period:
                    _, actual_number, actual_size, actual_color = fetch_actual_live_result()
                    
                    if actual_number is not None:
                        is_win = (predicted_size == actual_size)
                        
                        result_text = (
                            f"📊 **Result Update**\n\n"
                            f"📌 **Period:** {old_period}\n"
                            f"🎲 **Number:** {actual_number} ({actual_size} - {actual_color})\n"
                        )
                        
                        if is_win:
                            result_text += f"🎉 **Status: WIN ✅ (Step {current_step})**"
                            current_step = 1
                            await context.bot.send_message(chat_id=CHANNEL_ID, text=result_text, parse_mode="Markdown")
                            if WIN_STICKER_ID:
                                await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=WIN_STICKER_ID)
                        else:
                            result_text += f"❌ **Status: LOSS ❌ (Step {current_step})**"
                            current_step += 1
                            if current_step > 3:
                                current_step = 1
                            await context.bot.send_message(chat_id=CHANNEL_ID, text=result_text, parse_mode="Markdown")
                            if LOSS_STICKER_ID:
                                await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=LOSS_STICKER_ID)

            predicted_size = random.choice(["BIG", "SMALL"])
            
            signal_msg = (
                f"🚀 **VIP WinGo Signal** 🚀\n\n"
                f"🆔 **Period:** `{next_period}`\n"
                f"🎯 **Prediction:** **{predicted_size}**\n"
                f"📈 **Step:** {current_step}\n\n"
                f"🔗 [Register Here]({REGISTRATION_LINK})"
            )
            
            await context.bot.send_message(chat_id=CHANNEL_ID, text=signal_msg, parse_mode="Markdown", disable_web_page_preview=True)
            
            last_signal_data = {
                "period": next_period,
                "size": predicted_size
            }
            
        except Exception as e:
            print(f"Loop Error: {e}")
            
        await asyncio.sleep(60)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text("✅ আপনি ইতিমধ্যে ভেরিফাইয়েড আছেন! বট ব্যাকগ্রাউন্ডে কাজ করছে।")
        return
        
    await update.message.reply_text("🔑 **বটটি ব্যবহার করতে পাসওয়ার্ড দিন:**", parse_mode="Markdown", reply_markup=ForceReply(selective=True))

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global loop_started
    user_id = update.effective_user.id
    user_input = update.message.text
    
    if user_id in AUTHORIZED_USERS:
        return
        
    if user_input == BOT_PASSWORD:
        AUTHORIZED_USERS.add(user_id)
        await update.message.reply_text("🎉 **পাসওয়ার্ড সঠিক হয়েছে! সিগন্যাল শুরু হচ্ছে...**", parse_mode="Markdown")
        
        if not loop_started:
            loop_started = True
            asyncio.create_task(auto_signal_loop(context))
    else:
        await update.message.reply_text("❌ **ভুল পাসওয়ার্ড! আবার চেষ্টা করুন।**", parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
    
    print("✅ Complete Signal Bot Ready!")
    app.run_polling()
