"""Jarvis-AI Telegram bot entry (aiogram 3 polling)."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from ai.grok import GrokClient
from ai.memory import ConversationMemory
from config import ensure_directories, get_settings
from database.sqlite import Database, set_db
from logging_setup import setup_logging
from plugins.base import PluginManager
from plugins.docker import DockerPlugin
from plugins.files import FilesPlugin
from plugins.github import GitHubPlugin
from internal_server import start_internal_server
from telegram.commands import BOT_COMMANDS
from telegram.handlers import AuthMiddleware, bootstrap_product, build_router

logger = logging.getLogger(__name__)


async def run_bot() -> None:
    settings = get_settings()
    ensure_directories(settings)
    setup_logging(settings.log_level, settings.logs_dir)

    logger.info(
        "Starting %s | provider=%s model=%s",
        settings.app_name,
        settings.provider,
        settings.resolved_model,
    )
    logger.info("Owners: %s", sorted(settings.owner_ids))
    if settings.vietqr_pay_url:
        logger.info("VietQR Pay URL: %s", settings.vietqr_pay_url)

    db = Database(settings)
    await db.init()
    set_db(db)
    await bootstrap_product(settings)

    grok = GrokClient(settings)
    memory = ConversationMemory(settings)

    plugins = PluginManager()
    plugins.register(FilesPlugin(settings.workspace_dir))
    plugins.register(GitHubPlugin(settings.workspace_dir))
    plugins.register(DockerPlugin())
    await plugins.setup_all()

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )
    dp = Dispatcher()
    auth = AuthMiddleware(settings)
    dp.message.middleware(auth)
    dp.callback_query.middleware(auth)
    dp.include_router(build_router(settings, grok, memory))

    await bot.set_my_commands(BOT_COMMANDS)

    webhook_runner = None
    try:
        webhook_runner = await start_internal_server(bot, settings)
        me = await bot.get_me()
        logger.info("Bot @%s ready — polling…", me.username)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        logger.info("Shutting down…")
        if webhook_runner is not None:
            await webhook_runner.cleanup()
        await plugins.teardown_all()
        await grok.aclose()
        await db.close()
        await bot.session.close()


def main() -> None:
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\nBye.")


if __name__ == "__main__":
    main()
