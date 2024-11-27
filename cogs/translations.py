import gettext
import logging
from typing import Dict, List, Optional, Union

import babel
from babel import Locale as Locale
from babel.numbers import (
    format_compact_decimal as babel_format_compact_decimal,
    format_decimal as babel_format_decimal,
    format_percent as babel_format_percent,
)
from discord import Locale as DiscordLocale, app_commands
import discord
from discord.ext import commands

from utils import BotU, CogU, ContextU, emojidict, formatter, hybrid_command, GUILDS, Cooldown


# CHINESE_SIMPLIFIED = gettext.translation("translations/zh_CN", languages=['zh_CN'])
# CHINESE_TRADITIONAL = gettext.translation("", languages=['zh_TW'])

translation_logger = logging.getLogger('translation')
translation_logger.setLevel(logging.INFO)
translation_handler = logging.FileHandler('translation.log')
translation_handler.setFormatter(formatter)
translation_logger.addHandler(translation_handler)

async def skip_translate(s) -> str:
    """Method that just returns what was passed in.
    This method is intended to be used as a "pass" callback for interaction.translate where there is no interaction.
    Intentionally not typed so any STR like instance can be passed without type error.
    """
    return s

async def get_translation_callable(interaction: Optional[discord.Interaction]=None):
    """Returns the translate method for an interaction, or an async method that just returns what was passed in if no interaction is provided.
    """
    if interaction:
        return interaction.translate
    return skip_translate

def get_locale_info(locale: DiscordLocale) -> Locale:
    """Returns the locale info for a DiscordLocale.
    Uses Babel to get locale information.
    """
    return Locale.parse(str(locale.value), sep='-')

# @deprecated("Use format_decimal instead")
# def format_int(n: int, locale: DiscordLocale=DiscordLocale.american_english, **kwargs) -> str:
#     locale_info = get_locale_info(locale)
#     return babel_format_number(n, locale=locale_info, **kwargs)

def format_int(n: int, locale: DiscordLocale=DiscordLocale.american_english, **kwargs) -> str:
    locale_info = get_locale_info(locale)
    return babel_format_decimal(n, locale=locale_info, **kwargs)

def format_decimal(n: float, locale: DiscordLocale=DiscordLocale.american_english, **kwargs) -> str:
    locale_info = get_locale_info(locale)
    return babel_format_decimal(n, locale=locale_info, **kwargs)

def format_percentage(n: float, locale: DiscordLocale=DiscordLocale.american_english, **kwargs) -> str:
    locale_info = get_locale_info(locale)
    return babel_format_percent(n, locale=locale_info, **kwargs)

format_percent = format_percentage

def format_compact_decimal(n: float, locale: DiscordLocale=DiscordLocale.american_english, **kwargs) -> str:
    locale_info = get_locale_info(locale)
    return babel_format_compact_decimal(n, locale=locale_info, **kwargs)

def format_number(n: Union[int, float], locale: DiscordLocale=DiscordLocale.american_english, is_percentage: bool=False, is_compact_decimal: bool=False, **kwargs) -> str:
    if is_percentage:
        if 1 > n > 0:
            n = n * 100
        return format_percentage(n, locale=locale, **kwargs)
    elif is_compact_decimal:
        return format_compact_decimal(n, locale=locale, **kwargs)
    elif isinstance(n, int):
        return format_int(n, locale=locale, **kwargs)
    elif isinstance(n, float):
        return format_decimal(n, locale=locale, **kwargs)
    else:
        return str(n)

intcomma = format_int

SUPPORTED_LOCALES: List[DiscordLocale] = [
    #DiscordLocale.chinese,
]

LOCALE_FLAG_EMOJI_DICT: Dict[DiscordLocale, str] = {
    locale: emojidict.get(f"flag_{str(get_locale_info(locale).territory).lower()}", emojidict.get('question',''))
    for locale in DiscordLocale
    #for locale in SUPPORTED_LOCALES
}

class TranslatorCog(CogU, name="Translation Commands"):
    def __init__(self, bot: BotU):
        self.bot = bot
    
    @hybrid_command(name='locale', description="Shows you information about a locale.")
    @Cooldown(1, 5, commands.BucketType.user)
    @app_commands.guilds(*GUILDS)
    @app_commands.describe(locale="The locale to get information about.")
    async def locale(self, ctx: ContextU, *, locale: Optional[str]=None):
        """Shows you information about a Locale. If no locale is provided, it will show your locale (for slash commands)."""
        await ctx.defer()

        original_locale_input = locale

        is_guild_locale = False
        is_user_locale = False
        locale_obj = None
        babel_locale_obj = None

        if locale:
            try:
                locale_obj = discord.Locale(locale)
                assert locale_obj is not None
            except Exception:
                babel_locale_obj = babel.Locale.parse(locale, sep='-')
                if babel_locale_obj is None:
                    return await ctx.reply("That locale is not supported.",ephemeral=True)
                locale_obj = discord.Locale(babel_locale_obj.language)
        else:
            if ctx.interaction:
                is_user_locale = True
                locale_obj = ctx.interaction.locale
            elif ctx.guild:
                is_guild_locale = True
                locale_obj = ctx.guild.preferred_locale
    
        if locale_obj is None:
            return await ctx.reply("That locale is not supported.",ephemeral=True)

        if not babel_locale_obj:
            babel_locale_obj = get_locale_info(locale_obj)
        
        embed = discord.Embed()

        if is_user_locale:
            embed.title = f"Locale for {ctx.author}"
        elif is_guild_locale:
            embed.title = f"Guild Locale for {ctx.guild}"
        elif str(locale_obj.value).lower() == str(original_locale_input).lower().strip():
            embed.title = f"Locale Information for {locale_obj.value}"
        else:
            embed.title = f"Locale Information for {locale_obj.value} ({original_locale_input})"
        
        embed.add_field(name="Discord Internal Name", value=f"{locale_obj.name}", inline=True)
        embed.add_field(name="Discord Language Code", value=f"{locale_obj.value}", inline=True)

        embed.add_field(name="Display Name", value=f"{babel_locale_obj.get_display_name('en')}", inline=True)

        if babel_locale_obj.territory:
            embed.add_field(name="Territory", value=f"{babel_locale_obj.territory} {LOCALE_FLAG_EMOJI_DICT.get(locale_obj)}", inline=True)

        embed.add_field(name="Language", value=f"{babel_locale_obj.language}", inline=True)

        return await ctx.reply(embed=embed)
    
    # @hybrid_command(name=locale_str("commandname", location='hybrid_command name', description=locale_str("commanddescription", location='hybrid_command description')))
    # async def test(self, ctx):
    #     pass

class TranslatorU(app_commands.Translator):
    translations_dict: Dict[DiscordLocale, gettext.GNUTranslations] = {}

    locale_info: Dict[DiscordLocale, Locale] = {locale: get_locale_info(locale) for locale in SUPPORTED_LOCALES}

    @property
    def locales(self) -> List[DiscordLocale]:
        return list(self.translations_dict.keys())
    
    @property
    def translations(self) -> List[gettext.GNUTranslations]:
        return list(self.translations_dict.values())
    
    async def load(self) -> None:
        for locale in SUPPORTED_LOCALES:
            try:
                translation = gettext.translation("messages", localedir='locales', languages=[locale.value.lower()], fallback=True)
                translation.install()
                self.translations_dict[locale] = translation
                translation_logger.info(f'Loaded translation for {locale}')
            except FileNotFoundError:
                translation_logger.warning(f'No translation file found for {locale}, remove from supported_locales')
        translation_logger.info('Finished loading translations')

    async def unload(self) -> None:
        # for locale in SUPPORTED_LOCALES:
        #     translation = self.translations.get(locale)
        #     if translation:
        #         translation.remove()
        #         translation_logger.info(f'Unloaded translation for {locale}')
        # translation_logger.info('Finished unloading translations')
        self.translations_dict = {}

    async def translate(self, string: app_commands.locale_str, locale: DiscordLocale, context: app_commands.TranslationContextTypes) -> Optional[str]:
        #print("Ran", string, str(locale), context.location)
        translation = None

        if locale in self.locales:
            translation = self.translations_dict.get(locale)
            
            if translation:            
                translated_string = translation.gettext(string.message)

                if translated_string and translated_string != string.message:
                    translation_logger.info(f"Translated {string.message} to {translated_string} in {locale} at {context.location}")
                    return translated_string
                # else:
                #     translation_logger.warning(f"Translation not found for {string.message} in {locale} at {context.location}")
            else:
                translation_logger.error(f"Translations not found for supported locale {locale} at {context.location}. Remove from supported_locales.")
        # else:
        #     translation_logger.warning(f"Translation not found for {string.message} in {locale} at {context.location}")

        if context.location is app_commands.TranslationContextLocation.other:
            translation_logger.warning(f"Translation not found for {string.message} in {locale} at {context.location}. Returning original string.")
            return string.message

        translation_logger.warning(f"Translation not found for {string.message} in {locale} at {context.location}. Returning None.")
        return None
        # we can't return none because it actually returns None if it can't find a translation

async def setup(bot: BotU):
    cog = TranslatorCog(bot)
    await bot.add_cog(cog)
