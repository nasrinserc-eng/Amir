import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# راه‌اندازی لاگ برای دیدن خطاها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- بخش تنظیمات ---
TELEGRAM_BOT_TOKEN = "8360202192:AAGK3SqheE4wYqKx1-eeggvdyhf580jv6WQ"  # توکن ربات خود را اینجا قرار دهید

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """این تابع با دستور /start اجرا می‌شود."""
    user = update.effective_user
    await update.message.reply_html(
        f"سلام {user.mention_html()}!\n\n"
        f"اسم آهنگ یا لینک یوتیوب مورد نظرت رو بفرست تا برات دانلود کنم.",
    )

async def search_and_send_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """موزیک را جستجو، دانلود و برای کاربر ارسال می‌کند."""
    query = update.message.text
    chat_id = update.message.chat_id

    # به کاربر اطلاع می‌دهیم که فرآیند شروع شده است
    processing_message = await update.message.reply_text("در حال جستجو و پردازش... لطفاً کمی صبر کنید.")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{chat_id}_%(title)s.%(ext)s',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'logger': logger,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if "http" not in query:
                search_result = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if not search_result['entries']:
                    await processing_message.edit_text("متاسفانه آهنگی با این نام پیدا نشد.")
                    return
                video_url = search_result['entries'][0]['webpage_url']
                info = ydl.extract_info(video_url, download=True)
            else:
                info = ydl.extract_info(query, download=True)
        
        base_filename = ydl.prepare_filename(info).rsplit('.', 1)[0]
        audio_file_path = base_filename + '.mp3'
        
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError("فایل دانلود شده پیدا نشد!")

        await processing_message.edit_text("در حال ارسال فایل صوتی...")
        await context.bot.send_audio(
            chat_id=chat_id,
            audio=open(audio_file_path, 'rb'),
            title=info.get('title', 'Music'),
            duration=info.get('duration', 0)
        )

        os.remove(audio_file_path)
        await processing_message.delete()

    except Exception as e:
        logger.error(f"Error processing '{query}': {e}")
        await processing_message.edit_text(f"یک خطای غیرمنتظره رخ داد. لطفاً دوباره تلاش کنید.\n\nError: {e}")
        for file in os.listdir('.'):
            if file.startswith(str(chat_id)):
                os.remove(file)

# تعریف تابع اصلی ربات
def main() -> None:
    """این تابع اصلی، ربات را استارت می‌زند."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_and_send_music))

    # ربات را در حالت polling اجرا می‌کند
    application.run_polling()

# این بخش نقطه شروع اجرای برنامه است
# این خط باید در ابتدایی‌ترین سطح (بدون هیچ فاصله‌ای) باشد
if __name__ == '__main__':
    # این خط باید یک تورفتگی (معمولا 4 فاصله) داشته باشد
    main()