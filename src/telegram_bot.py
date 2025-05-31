import logging
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler
import random
import dateparser
import pytz
from tzlocal import get_localzone

# Import your Brain and Agent classes
from Core.brain import Brain
from Core.agent import Agent

# Load environment variables
load_dotenv("DataHub/.env")
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
USER_CHAT_ID = int(os.getenv('USER_CHAT_ID'))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.Formatter.converter = lambda *args: datetime.now(get_localzone()).timetuple()
logger = logging.getLogger(__name__)

class MIKATATelegramBot:
    def __init__(self):
        self.brain = Brain()
        self.agent = Agent(self.brain)

        self.local_tz = get_localzone()
        now = datetime.now(self.local_tz)
        self.last_user_message_time = now
        self.last_proactive_sent_time = now - timedelta(hours=random.uniform(1, 3))

        self.loop = asyncio.get_event_loop()
        self.bot = None
        self.scheduler = BackgroundScheduler()

        initial_delay_hours = random.uniform(2.5, 4.0)
        first_run_time = now + timedelta(hours=initial_delay_hours)
        self.scheduler.add_job(
            self.schedule_next_proactive_check_in,
            'date',
            run_date=first_run_time,
            args=[True],
            id='proactive_rescheduler'
        )
        logger.info(f"First proactive check-in scheduled for: {first_run_time} (in {initial_delay_hours:.2f} hours)")
        self.scheduler.start()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Hello! I'm MIKATA, your caring and loyal AI companion. How can I assist you today?")
        self.last_user_message_time = datetime.now(self.local_tz)

    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat.id != USER_CHAT_ID:
            await update.message.reply_text("I'm sorry, I can only chat with my designated user.")
            return

        try:
            user_message = update.message.text
            self.last_user_message_time = datetime.now(self.local_tz)
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            await asyncio.sleep(random.uniform(0.5, 2.0))

            response_text, scheduling_instruction = await self.agent.process_user_input(user_message)

            if scheduling_instruction:
                await self.handle_scheduling_request(scheduling_instruction, update.effective_chat.id)
                await update.message.reply_text(response_text)
            else:
                await update.message.reply_text(response_text)

        except Exception as e:
            logger.error(f"Error in chat handler: {e}", exc_info=True)
            await update.message.reply_text("Oops! Something went wrong. Please try again later.")

    async def handle_scheduling_request(self, instruction: dict, chat_id: int):
        action = instruction.get("action")
        time_expression = instruction.get("time_expression")
        specific_message = instruction.get("specific_message")

        parsed_time = dateparser.parse(
            time_expression,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': datetime.now(self.local_tz),
                'TIMEZONE': str(self.local_tz),
                'TO_TIMEZONE': str(self.local_tz),
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )


        if not parsed_time:
            logger.error(f"Failed to parse time expression '{time_expression}'")
            await self.bot.send_message(chat_id=chat_id, text="Couldn't understand the time. Please rephrase.")
            return

        if parsed_time <= datetime.now(self.local_tz) and "today" not in time_expression.lower():
            parsed_time += timedelta(days=1)

        job_id = f"{action}_{parsed_time.isoformat()}_{random.randint(1000, 9999)}"
        self.brain.memory_management.add_scheduled_event(job_id, action, parsed_time, specific_message)

        if self.scheduler.get_job('user_scheduled_event'):
            try:
                self.scheduler.remove_job('user_scheduled_event')
            except Exception as e:
                logger.warning(f"Could not remove old job: {e}")

        self.scheduler.add_job(
            lambda: asyncio.run_coroutine_threadsafe(
                self.execute_scheduled_event(chat_id, action, specific_message, job_id),
                self.loop
            ),
            'date',
            run_date=parsed_time,
            id='user_scheduled_event'
        )

        logger.info(f"Scheduled '{action}' for {parsed_time.strftime('%Y-%m-%d %I:%M %p %Z')} with message: '{specific_message}'")

    async def execute_scheduled_event(self, chat_id: int, action: str, specific_message: str | None, job_id: str):
        now = datetime.now(self.local_tz)
        logger.info(f"Executing '{action}' (Job ID: {job_id}) at {now.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
        self.brain.memory_management.deactivate_scheduled_event(job_id)

        internal_query_to_brain = ""
        if specific_message:
            internal_query_to_brain = f"Scheduled reminder: '{specific_message}'"
        elif action == "schedule_reminder":
            internal_query_to_brain = "General reminder triggered."
        elif action == "pause_conversation":
            internal_query_to_brain = f"'Pause conversation' period ended at {now.strftime('%I:%M %p')}."

        final_bot_response, _ = self.brain.generate_response(internal_query_to_brain, {"alt_prompt_mode": True, "scheduled_event_follow_up": True, "action": action})

        try:
            await self.bot.send_message(chat_id=chat_id, text=final_bot_response)
            self.last_proactive_sent_time = now
        except Exception as e:
            logger.error(f"Error sending scheduled event: {e}")

    async def schedule_next_proactive_check_in(self, initial_run=False) -> None:
        if not initial_run:
            asyncio.run_coroutine_threadsafe(self.proactive_check_in_logic(), self.loop).result()

        next_delay_hours = random.uniform(2.0, 5.0)
        next_run_time = datetime.now(self.local_tz) + timedelta(hours=next_delay_hours)

        if self.scheduler.get_job('proactive_rescheduler'):
            self.scheduler.remove_job('proactive_rescheduler')

        self.scheduler.add_job(
            self.schedule_next_proactive_check_in,
            'date',
            run_date=next_run_time,
            args=[False],
            id='proactive_rescheduler'
        )
        logger.info(f"Next proactive check-in scheduled for: {next_run_time.strftime('%Y-%m-%d %I:%M %p %Z')}")

    async def proactive_check_in_logic(self) -> None:
        now = datetime.now(self.local_tz)
        time_since_last_user_message = now - self.last_user_message_time
        time_since_last_proactive_sent = now - self.last_proactive_sent_time

        active_event = self.brain.memory_management.get_active_scheduled_event()
        if active_event and active_event["is_active"] and active_event["action"] == "pause_conversation" and now < active_event["trigger_time"]:
            logger.info(f"Proactive suppressed due to active 'pause_conversation' until {active_event['trigger_time'].strftime('%Y-%m-%d %I:%M %p %Z')}")
            return

        if time_since_last_user_message > timedelta(hours=1) and time_since_last_proactive_sent > timedelta(hours=2):
            current_hour = now.hour
            if 5 <= current_hour < 12:
                greeting = "Good morning!"
            elif 12 <= current_hour < 18:
                greeting = "Good afternoon!"
            else:
                greeting = "Good evening!"

            try:
                prompt = (
                    f"{greeting} The user hasn't messaged in {time_since_last_user_message.total_seconds() / 3600:.1f} hours. "
                    "Generate a warm and thoughtful check-in."
                )
                response, _ = self.brain.generate_response(prompt, {"alt_prompt_mode": True})

                if self.bot and self.bot.get_chat(USER_CHAT_ID):
                    await self.bot.send_message(chat_id=USER_CHAT_ID, text=response)
                    self.last_proactive_sent_time = now
            except Exception as e:
                logger.error(f"Proactive message error: {e}")

    def run(self) -> None:
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        if not USER_CHAT_ID:
            raise ValueError("USER_CHAT_ID not found or invalid")

        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.bot = app.bot

        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chat))
        app.add_error_handler(self.error_handler)

        logger.info("Starting MIKATA Telegram bot...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.error(f"Update {update} caused error: {context.error}", exc_info=True)

if __name__ == '__main__':
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    bot = MIKATATelegramBot()
    bot.run()
