import logging
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler
from Core.brain import Brain

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
USER_CHAT_ID = int(os.getenv('USER_CHAT_ID'))  # Make sure it's an integer!
 
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class MIKATATelegramBot:
    def __init__(self):
        self.brain = Brain()
        self.last_user_message_time = datetime.utcnow()
        self.last_proactive_sent_time = datetime.utcnow() - timedelta(hours=1)  # Optional cooldown
        self.loop = asyncio.get_event_loop()  # Save event loop for background thread access
        self.bot = None  # Will be assigned in run()

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.proactive_check_in, 'interval', hours=3)
        self.scheduler.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        welcome_message = "Hello! I'm MIKATA, your caring and loyal AI companion. How can I assist you today?"
        await update.message.reply_text(welcome_message)
        self.last_user_message_time = datetime.utcnow()

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            user_message = update.message.text
            self.last_user_message_time = datetime.utcnow()

            response = self.brain.generate_response(user_message, {})
            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await update.message.reply_text("I apologize, but I encountered an error processing your message.")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(f"Update {update} caused error: {context.error}")

    def proactive_check_in(self):
        logger.info("Proactive message initiated!")
        try:
            now = datetime.utcnow()
            diff = now - self.last_user_message_time

            if diff > timedelta(minutes=1):  # Proactive threshold
                hour = now.hour
                if 5 <= hour < 12:
                    time_msg = "Good morning! ☀️"
                    emotion = "cheerful"
                elif 12 <= hour < 18:
                    time_msg = "Hope your day’s going well 🌼"
                    emotion = "caring"
                elif 18 <= hour < 22:
                    time_msg = "Evening already! 🌆"
                    emotion = "soft"
                else:
                    time_msg = "Hey, still awake? 🌙"
                    emotion = "whispering"

                if diff > timedelta(hours=12):
                    mood_prompt = f"Send a worried message asking if everything is okay. MIKATA is concerned. Be gentle and {emotion}."
                elif diff > timedelta(hours=6):
                    mood_prompt = f"Send a heartfelt message as if MIKATA misses the user. Make it warm, emotional, and {emotion}."
                else:
                    mood_prompt = f"Send a casual check-in message in a {emotion} tone."

                final_prompt = f"{time_msg}\n\n{mood_prompt}"
                response = self.brain.generate_response(final_prompt, "alt_prompt")

                # ✅ Send message safely from background thread
                if self.bot and self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.bot.send_message(chat_id=USER_CHAT_ID, text=response),
                        self.loop
                    )
                    logger.info("Proactive message sent.")
                else:
                    logger.warning("Bot or event loop not initialized.")

        except Exception as e:
            logger.error(f"Error in proactive check-in: {str(e)}")

    def run(self):
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.bot = app.bot  # Save bot reference

        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))
        app.add_error_handler(self.error_handler)

        logger.info("Starting MIKATA Telegram bot...")
        app.run_polling()


if __name__ == "__main__":
    bot = MIKATATelegramBot()
    bot.run()
