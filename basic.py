import os
import logging
import re
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import instaloader

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Instaloader
L = instaloader.Instaloader()

# Extract shortcode from Instagram link
def extract_shortcode(link: str):
    """
    Extracts shortcode from an Instagram post/reel/TV URL.

    Examples:
    - https://www.instagram.com/reels/Cr9-ZxGJHGx/
    - https://www.instagram.com/p/Cr9-ZxGJHGx/?utm_source=ig_web_copy_link
    - https://www.instagram.com/tv/Cr9-ZxGJHGx
    - https://www.instagram.com/reel/Cr9-ZxGJHGx/
    """
    match = re.search(r"instagram\.com/(?:p|reels|reel|tv)/([A-Za-z0-9_-]+)", link)
    if match:
        return match.group(1)
    return None

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user and user.first_name else "there"

    welcome_message = f"""
        👋 Hi {name}!

        📥 To download an Instagram video, follow these steps:

        1️⃣ Copy the Instagram video URL  
        2️⃣ Paste it here using the /download command like this:  
        `/download https://www.instagram.com/reels/xyz/`

        ⚠️ Only public posts are supported.
    """
    await update.message.reply_text(welcome_message)

# /download command
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please provide an Instagram link.\nUsage: `/download <url>`", parse_mode='Markdown')
        return

    url = context.args[0]
    shortcode = extract_shortcode(url)

    if not shortcode:
        await update.message.reply_text("❌ Invalid Instagram URL. Please send a valid post, reel, or TV link.")
        return

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            await update.message.reply_video(post.video_url)
        else:
            await update.message.reply_photo(post.url)

    except Exception as e:
        logger.error("Error downloading post: %s", str(e))
        await update.message.reply_text("❌ Failed to fetch the media. Is the post public?\n\nError: " + str(e))

# Main function
def main():
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set.")
        print("Set it using: export TELEGRAM_BOT_TOKEN='your_token_here'")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("download", download))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
