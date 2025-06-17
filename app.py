import asyncio
import os

from aiogram.client.default import DefaultBotProperties
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommandScopeAllPrivateChats

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from database.engine import create_db, drop_db, session_maker


from middlewares.db import DataBaseSession

from common.bot_commands_list import private
from handlers.user_private import user_private_router
from handlers.reports import reports_router
from handlers.financial_calculator import finance_router
from handlers.profile import profile_router
from handlers.transfer import transfer_router
from handlers.account import account_router
from handlers.budget import budget_router
from handlers.recurring_payment import recurring_payment_router


bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(finance_router)
dp.include_router(reports_router)
dp.include_router(profile_router)
dp.include_router(transfer_router)
dp.include_router(account_router)
dp.include_router(budget_router)
dp.include_router(recurring_payment_router)

async def on_startup():
    run_param = False
    if run_param:
        await drop_db()

    await create_db()


async def on_shutdown():
    print('Бот лёг!')


async def tg_bot():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)  # не отвечает на сообщения,когда бот был офлайн
    await bot.set_my_commands(commands=private, scope=BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(tg_bot())
