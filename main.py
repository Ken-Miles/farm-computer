import discord
from discord.ext import commands

from src.config import (
    BOT_TOKEN,
    BOT_PREFIX,
    MAIN_SERVER,
    CMD_CHANS,
)

from src.logger import Logger
import src.wiki as _wiki
from src.embed import EmbedBuiler

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

logger = Logger('FarmComputer')

@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

@bot.command()
async def wiki(ctx, *args):
    await ctx.send(embed=_wiki.search(args, _logger=logger))

@bot.tree.command(
    name = "wiki",
    description = "Search the Stardew Valley Wiki for a specific page",
    guild=discord.Object(id=MAIN_SERVER)
)
async def wiki(interaction: discord.Interaction, query: str):
    # logger.info(f'wiki command called with query: {query}')
    logger.info(f'wiki command called in channel: {str(interaction.channel.id)}')
    logger.info(f'CMD_CHANS: {CMD_CHANS}')
    logger.info(f'ephemeral: {str(interaction.channel.id) not in CMD_CHANS}')
    await interaction.response.defer(
        ephemeral=str(interaction.channel.id) not in CMD_CHANS
    )
    await interaction.followup.send(
        embed=_wiki.search(query, _logger=logger),
    )


@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=MAIN_SERVER))
    logger.info(f'Bot is ready as {bot.user} ({bot.user.id})')
    print()

bot.run(BOT_TOKEN)