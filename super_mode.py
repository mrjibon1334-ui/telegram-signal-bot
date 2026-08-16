import asyncio
import random
import datetime
import cloudscraper
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8978017343:AAGcnXfBEn76BmCJULIn4U0Mm8cB5aLgrSM"
REGISTRATION_LINK = "https://dkwin7.com/#/register?invitationCode=82824101415"
ADMIN_USERNAME = "Adnan485825"
CHANNEL_ID = "@freedkwinsignal"

WIN_STICKER_ID = "CAACAgUAAxkBAAERs15qfadmESLSuDJuumUsWGD0RjIAATYAAkAhAAKQ_PhUDznfLhIsF809BA"
LOSS_STICKER_ID = "CAACAgUAAxkBAAERs2BqfaeLPNLeouIE50oOuD_oeJ4u_gACuB4AAlPb-VTHnZIszeTCaT0E"

is_channel_bot_running = False

def fetch_actual_live_result():
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json", timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", {}).get("list", [])
            if data:
                history = [("BIG" if int(item.get("number", 0)) >= 5 else "SMALL") for item in data[:10]]
                num = int(data[0].get("number", 0))
                period = str(data[0].get("issueNumber", ""))[-4:]
                size = "BIG" if num >= 5 else "SMALL"
                return period, num, size, history
    except:
        pass
    return None, None, None, []

def get_pro_prediction(history):
    if len(history) >= 3:
        if history[0] == history[1] == history[2]:
            return ("SMALL" if history[0] == "BIG" else "BIG"), "Pro Trend-Break"
        
        big_c = history.count("BIG")
        if big_c > 6: return "SMALL", "High BIG Intensity"
        if big_c < 4: return "BIG", "High SMALL Intensity"
            
    return ("BIG" if random.random() > 0.5 else "SMALL"), "Balanced Mode"

async def channel_signal_loop(context: ContextTypes.DEFAULT_TYPE):
    global is_channel_bot_running
    total_wins = 39 
    total_losses = 35 
    current_step = 1
    
    last_period = None
    last_pred = None
    last_sent_msg_id = None
    last_sent_text = ""

    while is_channel_bot_running:
        try:
            now = datetime.datetime.now()
            await asyncio.sleep(60 - now.second)
            if not is_channel_bot_running: break
            
            curr_period, curr_num, curr_size, history = fetch_actual_live_result()
            
            if last_period and last_pred:
                if curr_size:
                    is_win = (curr_size == last_pred)
                    if is_win:
                        total_wins += 1
                        current_step = 1
                        status_str = "✨ **WIN ✅**"
                    else:
                        total_losses += 1
                        current_step += 1
                        status_str = "❌ **LOSS**"

                    result_text = f"\n\n📊 Result: #{curr_period} -> {curr_num} ({curr_size})\nStatus: {status_str} | Step: {current_step}\n📈 Stats: W:{total_wins} | L:{total_losses}"
                    
                    if last_sent_msg_id:
                        try:
                            await context.bot.edit_message_text(chat_id=CHANNEL_ID, message_id=last_sent_msg_id, text=last_sent_text + result_text, parse_mode="Markdown")
                            if is_win: await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=WIN_STICKER_ID)
                            else: await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=LOSS_STICKER_ID)
                        except: pass

            pred, strategy = get_pro_prediction(history)
            last_period = curr_period
            last_pred = pred
            
            pred_msg = (f"🚀 **PRO ANALYSIS SIGNAL** 🚀\n"
                        f"📌 Period: `#{curr_period}`\n"
                        f"🎯 Prediction: **{pred}**\n"
                        f"⚙️ Strategy: `{strategy}`\n"
                        f"🔄 Step: `Step {current_step}`\n\n"
                        f"🔗 **Register:** [Click Here]({REGISTRATION_LINK})\n"
                        f"👤 **Admin Contact:** @{ADMIN_USERNAME}")

            try:
                msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=pred_msg, parse_mode="Markdown")
                last_sent_msg_id = msg.message_id
                last_sent_text = pred_msg
            except: pass
            
            await asyncio.sleep(5)
        except Exception as e:
            await asyncio.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_channel_bot_running
    user = update.effective_user
    
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        if not is_channel_bot_running:
            is_channel_bot_running = True
            asyncio.create_task(channel_signal_loop(context))
            await update.message.reply_text("✅ সিগন্যাল সার্ভিস চ্যানেলে চালু করা হয়েছে!")
        else:
            await update.message.reply_text("⚠️ বট ইতিমধ্যে চ্যানেলে চলছে।")
    else:
        await update.message.reply_text("👋 আমাদের চ্যানেলে যুক্ত থাকুন। সিগন্যাল সেখানেই পাওয়া যাবে।")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_channel_bot_running
    user = update.effective_user
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        is_channel_bot_running = False
        await update.message.reply_text("🛑 সিগন্যাল সার্ভিস বন্ধ করা হয়েছে।")
    else:
        await update.message.reply_text("❌ এই কমান্ডটি শুধুমাত্র অ্যাডমিনের জন্য।")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    
    print("বট সফলভাবে রান হচ্ছে!")
    app.run_polling()

if __name__ == '__main__':
    main()
