from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
import config
from ..logging import LOGGER


class Anony(Client):
    def __init__(self):
        LOGGER(__name__).info("Starting Bot...")

        super().__init__(
            name="AnonXMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
            proxy=config.PROXY if config.PROXY else None,
        )

    async def start(self):
        await super().start()

        self.id = self.me.id
        self.name = (self.me.first_name or "") + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            if config.LOGGER_ID:
                await self.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"<b>Bot Started</b>\nID: {self.id}\nName: {self.name}",
                )
        except Exception:
            pass

        try:
            if config.LOGGER_ID:
                a = await self.get_chat_member(config.LOGGER_ID, self.id)
                if a.status != ChatMemberStatus.ADMINISTRATOR:
                    LOGGER(__name__).error("Bot not admin in log group")
                    exit()
        except Exception:
            pass

        LOGGER(__name__).info(f"Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
