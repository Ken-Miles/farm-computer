import asyncio
import datetime
import time

import aiohttp
import discord
from discord.ext import commands
import environ
import yaml

from cogs import EXTENSIONS
from utils import BotU, Help, MentionableTree
from utils.custom_constants import handler

intents = discord.Intents.default()
intents.message_content = True

env = environ.Env(
    PROD=(bool, False),
)

PROD = env("PROD")

if PROD:
    with open("client.yml", "r") as f:
        token = dict(yaml.safe_load(f)).get("token")

prefixes = ["fc!"]

currentdate_epoch = int(time.time())
currentdate = datetime.datetime.fromtimestamp(currentdate_epoch)

if __name__ == "__main__":
    print(
    f"""Started running:
PROD: {PROD}
{currentdate}
{currentdate_epoch}"""
)

bot = BotU(
    command_prefix=commands.when_mentioned_or(*prefixes),
    intents=intents,
    activity=discord.Activity(type=discord.ActivityType.watching, name="the Rainbow Six Siege Pro League"),
    status=discord.Status.dnd,
    help_command=Help(),
    tree_cls=MentionableTree,
)
tree = bot.tree

@bot.event
async def on_ready():
    date = datetime.datetime.fromtimestamp(int(time.time()))
    print(f"{date}: Ready!")

async def main():
    #if PROD:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        from utils import SENTRY_URL

        sentry_sdk.init(
            dsn=SENTRY_URL,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=.5,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=.5,

            environment="production" if PROD else "development",

            integrations=[
                AsyncioIntegration(),
            ],

            _experiments={
                "profiles_sample_rate": .5, #type: ignore
            },
        )
    except ImportError:
        pass

    async with aiohttp.ClientSession() as session:
        async with aiohttp.ClientSession() as session2:
            async with aiohttp.ClientSession() as session3:
                bot.session = session
                bot.session2 = session2
                bot.session3 = session3
                discord.utils.setup_logging(handler=handler)
                for file in EXTENSIONS:
                    await bot.load_extension(file)
                    #bot_logger.debug(f"Loaded extension {file}")
                await bot.load_extension("jishaku")
                #bot_logger.debug("Loaded extension jishaku")
                # await bot.load_extension("utils.cogs.error_handler")
                # bot_logger.debug("Loaded extension utils.cogs.error_handler")
                await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
