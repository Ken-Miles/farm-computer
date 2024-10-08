from __future__ import annotations
import datetime
from typing import Dict, Optional, Tuple, Type, Union

import discord
import environ
from tortoise import Tortoise, fields
from tortoise.models import Model
from typing_extensions import Self


class Base(Model):
    id = fields.BigIntField(pk=True, unique=True, generated=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True

class SettingsInfo(Base):
    name = fields.CharField(max_length=100)
    description = fields.CharField(max_length=100)

    valuetype = fields.CharField(max_length=100)
    """The type of the value. Can be 'str', 'int', 'bool', 'float', 'datetime', 'date', 'time', 'duration'."""

    emoji = fields.CharField(max_length=100, null=True)
    """The emoji to use for the setting."""

    min_value = fields.IntField(null=True)
    """The minimum value for the setting."""

    max_value = fields.IntField(null=True)
    """The maximum value for the setting."""

    active = fields.BooleanField(default=True)
    """Whether the setting is active."""

    @classmethod
    async def all_active(cls):
        return await cls.filter(active=True)

    class Meta:
        table = "SettingsInfo"

class Settings(Base):
    user_id = fields.BigIntField(unique=True)
    username = fields.CharField(max_length=100)


    preferred_platform = fields.CharField(max_length=5,default='N/A')
    show_on_leaderboard = fields.BooleanField(default=True)

    prefix = fields.CharField(max_length=5, default="!")
    use_custom_prefix = fields.BooleanField(default=False)

    show_prefix_command_tips = fields.BooleanField(default=True)

    language = fields.CharField(max_length=5, default="en")
    timezone = fields.CharField(max_length=50, default="UTC")
    color = fields.CharField(max_length=7, default="#7289DA")

    @property
    def all_settings(self) -> Dict[str, Tuple[Union[str, int, bool], Type]]:
        """All Settings for a user. 

        Returns:
            Dict[str, Tuple[Union[str, int, bool], Type]]: Returns a dictionary:
            {
                "setting_name": (setting_value, setting_type)
            }
        """        
        settings: Dict[str, Tuple[Union[str, int, bool], Type]] = {}

        for attr in self._meta.fields:
            if attr not in IGNORED_FIELDS:
                settings[attr] = getattr(self, attr), type(getattr(self, attr))
        return settings

    def get_setting_value(self, setting: str) -> str:
        """Get the name of a setting.

        Args:
            setting (str): The setting to get the name for.

        Returns:
            str: The setting name.
        """        
        return getattr(self, setting)

    def set_setting_value(self, setting: str, value: Union[str, int, bool]) -> None:
        """Set a setting for a user.

        Args:
            setting (str): The setting to set.
            value (Union[str, int, bool]): The value to set the setting to.
        """        
        return setattr(self, setting, value)

    def get_setting_type(self, setting: str) -> Type:
        """Get a setting for a user.

        Args:
            setting (str): The setting to get.

        Returns:
            Union[str, int, bool]: The setting value.
        """        
        return type(getattr(self, setting))

    async def get_setting_info_for(self, setting: str) -> Optional[SettingsInfo]:
        """Get the settings info for a setting.

        Args:
            setting (str): The setting to get the info for.

        Returns:
            Optional[SettingsInfo]: The settings info.
        """
        return await SettingsInfo.filter(name=setting).first()

    class Meta:
        table = "Settings"

class CommandInvocation(Base):
    transaction_id = fields.UUIDField(null=True)

    command_id = fields.BigIntField()

    prefix = fields.CharField(max_length=25, null=True)
    is_slash = fields.BooleanField(default=False)

    user_id = fields.BigIntField()
    guild_id = fields.BigIntField(null=True)
    channel_id = fields.BigIntField(null=True)    
    
    command = fields.CharField(max_length=100)

    args = fields.JSONField()
    kwargs = fields.JSONField()
    timestamp = fields.DatetimeField()

    completed = fields.BooleanField(null=True)
    completion_timestamp = fields.DatetimeField(null=True)

    error = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "CommandInvocations"


class Commands(Base):
    # id SERIAL PRIMARY KEY,
    # guild_id BIGINT,
    # channel_id BIGINT,
    # author_id BIGINT,
    # used TIMESTAMP,
    # prefix TEXT,
    # command TEXT,
    # failed BOOLEAN
    # app_command BOOLEAN NOT NULL DEFAULT FALSE
    # args TEXT,

    guild_id = fields.BigIntField(null=True)
    @property
    def guild(self):
        return self.guild_id

    channel_id = fields.BigIntField(null=True)
    @property
    def channel(self):
        return self.channel_id

    author_id = fields.BigIntField()
    @property
    def author(self):
        return self.author_id

    used = fields.DatetimeField()
    uses = fields.BigIntField(default=1)
    prefix = fields.CharField(max_length=23)
    command = fields.CharField(max_length=100)
    failed = fields.BooleanField(default=False)
    app_command = fields.BooleanField(default=False)
    args = fields.JSONField(null=True)
    kwargs = fields.JSONField(null=True)

    @classmethod
    async def bulk_insert(cls, bulk_data: list[dict]):
        # self._data_batch.append(
        #         {
        #             'guild': guild_id,
        #             'channel': ctx.channel.id,
        #             'author': ctx.author.id,
        #             'used': message.created_at.isoformat(), # created_at 
        #             'prefix': ctx.prefix,
        #             'command': command,
        #             'failed': ctx.command_failed,
        #             'app_command': is_app_command,
        #             'args': ctx.args,
        #             'kwargs': ctx.kwargs,
        #         }
        #     )
        if not bulk_data:
            return
        
        #models_list = []

        for data in bulk_data:
            if data.get("guild",None):
                data["guild_id"] = data.pop("guild")
            if data.get("channel",None):
                data["channel_id"] = data.pop("channel")
            if data.get("author",None):
                data["author_id"] = data.pop("author")
            #models_list.append(cls(**data))
            #data['uses'] = await cls.filter(guild_id=data.get("guild_id"), command=data.get("command")).count() + 1
            await cls.create(**data)
        #await cls.bulk_create(models_list, batch_size=1000)
        
    class Meta:
        table = "Commands"

class Blacklist(Base):
    offender_id = fields.BigIntField()
    offender_name = fields.CharField(max_length=100, null=True)
    reason = fields.CharField(max_length=255, null=True)
    timestamp = fields.DatetimeField()

    @classmethod
    async def add(cls, user: discord.abc.User, reason: Optional[str]=None) -> Self:
        instance, _ = await cls.update_or_create(
            defaults={
                'offender_id': user.id,
                'offender_name': user.name,
                'reason': reason,
                'timestamp': datetime.datetime.now(),
            }
        )
        return instance

    @classmethod
    async def remove(cls, user: int) -> bool:
        instance = await cls.filter(offender_id=user).first()
        if instance:
            await instance.delete()
        return not instance

    @classmethod
    async def is_blacklisted(cls, id: int) -> bool:
        return await cls.filter(offender_id=id).exists()

    @classmethod
    async def blacklisted(cls, id: int) -> Optional[Self]:
        return await cls.filter(offender_id=id).first()

    class Meta:
        table = "Blacklist"

class ReportedErrors(Base):
    """Errors Reported to my private forum via that menu thing."""

    error_id = fields.UUIDField()

    user_id = fields.BigIntField()

    forum_id = fields.BigIntField()
    forum_post_id = fields.BigIntField()
    forum_initial_message_id = fields.BigIntField()

    error_message = fields.TextField(null=True)

    resolved = fields.BooleanField(default=False)

    class Meta:
        table = "ReportedErrors"


class DiscordGuilds(Base):
    # id 
    # created_at
    # updated_at

    # basic guild info 
    guild_id = fields.BigIntField(unique=True)
    """The ID of the guild."""

    name = fields.CharField(max_length=256)
    """The guild name."""

    guild_created_at = fields.DatetimeField()
    """When the guild was created."""

    description = fields.TextField(null=True)
    """The description of the guild."""

    owner = fields.ForeignKeyField('my_app.DiscordUsers', related_name='owner', null=True)
    """The owner of the guild."""

    guild_owner_id = fields.BigIntField(null=True)
    """The ID of the owner of the guild."""

    # features
    features = fields.JSONField(null=True)
    """The features of the guild."""

    vanity_url = fields.CharField(max_length=256, null=True)
    """The vanity URL of the guild."""

    vanity_url_code = fields.CharField(max_length=256, null=True)
    """The vanity URL code of the guild."""

    # stats
    approximate_member_count = fields.BigIntField(null=True)
    """The approximate number of members in the guild. This is None unless the guild is obtained using Client.fetch_guild() or Client.fetch_guilds() with with_counts=True."""

    member_count = fields.BigIntField(null=True)
    """Returns the member count if available.
    Due to a Discord limitation, in order for this attribute to remain up-to-date and accurate, it requires Intents.members to be specified."""

    approximate_presence_count = fields.BigIntField(null=True)
    """The approximate number of members currently active in the guild. Offline members are excluded. This is None unless the guild is obtained using Client.fetch_guild() or Client.fetch_guilds() with with_counts=True."""

    # limits
    max_members = fields.BigIntField(null=True)
    """The maximum amount of members the guild can have."""

    max_presences = fields.BigIntField(null=True)
    """The maximum amount of presences the guild can have.
    Only available with .fetch_guilds()"""

    max_video_channel_users = fields.BigIntField(null=True)
    """The maximum amount of users in a video channel the guild can have."""

    bitrate_limit = fields.FloatField(null=True)
    """The maximum bitrate for voice channels this guild can have."""

    filesize_limit = fields.BigIntField(null=True)
    """The maximum number of bytes files can have when uploaded to this guild."""

    sticker_limit = fields.BigIntField(null=True)
    """The maximum number of sticker slots this guild has."""

    emoji_limit = fields.BigIntField(null=True)
    """The maximum number of emoji this guild can have."""

    # settings

    afk_timeout = fields.BigIntField(null=True)
    """The number of seconds until someone is moved to the AFK channel."""
    # afk channel later

    verification_level = fields.IntField(null=True)
    """The guild's verification level."""

    explicit_content_filter = fields.IntField(null=True)
    """The guild's explicit content filter level."""

    default_notifications = fields.IntField(null=True)
    """The guild's notification settings."""

    premium_tier = fields.IntField(null=True)
    """The premium tier for this guild. Corresponds to “Nitro Server” in the official UI. The number goes from 0 to 3 inclusive."""

    premium_subscription_count = fields.BigIntField(null=True)
    """The number of boosts this guild currently has."""

    preferred_locale = fields.CharField(max_length=30, null=True)
    """The preferred locale for the guild. Used when filtering Server Discovery results to a specific language."""

    nsfw_level = fields.IntField(null=True)
    """The guild's NSFW level."""

    mfa_level = fields.IntField(null=True)
    """The guild's MFA level."""

    premium_progress_bar_enabled = fields.BooleanField(default=False, null=True)
    """Whether the premium progress bar is enabled or not."""

    widget_enabled = fields.BooleanField(default=False, null=True)
    """Whether the widget is enabled or not."""

    premium_progress_bar_enabled = fields.BooleanField(default=False, null=True)
    """Whether the premium progress bar is enabled or not."""
    
    # channels
    afk_channel_id = fields.BigIntField(null=True)
    """The ID of the AFK channel."""

    system_channel_id = fields.BigIntField(null=True)
    """The ID of the system channel."""

    system_channel_flags = fields.BigIntField(null=True)
    """The system channel flags."""

    rules_channel_id = fields.BigIntField(null=True)
    """Returns the guild's channel used for the rules. The guild must be a Community guild.
    If no channel is set, then this returns None."""

    public_updates_channel_id = fields.BigIntField(null=True)
    """Returns the guild's channel where admins and moderators of the guilds receive notices from Discord. The guild must be a Community guild.
    If no channel is set, then this returns None."""

    safety_alerts_channel_id = fields.BigIntField(null=True)
    """Returns the guild's channel used for safety alerts, if set.
    For example, this is used for the raid protection setting. The guild must have the COMMUNITY feature."""

    widget_channel_id = fields.BigIntField(null=True)
    """Returns the widget channel of the guild.
    If no channel is set, then this returns None."""

    # roles
    default_role_id = fields.BigIntField(null=True)
    """The ID of the default role of the guild."""

    premium_subscriber_role_id = fields.BigIntField(null=True)
    """Gets the premium subscriber role, AKA “boost” role, in this guild."""
    
    # self_role in bot guild info

    # timeout/security
    invited_paused_until = fields.DatetimeField(null=True)
    """Returns the time when the guild's invites were paused. If invites are not paused, this returns None."""

    dms_paused_until = fields.DatetimeField(null=True)
    """Returns the time when the guild's DMs were paused. If DMs are not paused, this returns None."""

    # images
    icon_url = fields.CharField(max_length=1024, null=True)
    """The URL of the guild's icon."""

    icon_bytes = fields.BinaryField(null=True)
    """The guild's icon, represented as bytes."""

    banner_url = fields.CharField(max_length=1024, null=True)
    """The URL of the guild's banner."""

    banner_bytes = fields.BinaryField(null=True)
    """The guild's banner, represented as bytes."""

    splash_url = fields.CharField(max_length=1024, null=True)
    """The URL of the guild's splash."""

    splash_bytes = fields.BinaryField(null=True)
    """The guild's splash, represented as bytes."""

    discovery_splash_url = fields.CharField(max_length=1024, null=True)
    """The URL of the guild's discovery splash."""

    discovery_splash_bytes = fields.BinaryField(null=True)
    """The guild's discovery splash, represented as bytes."""

    # guild info relating to the bot
    self_role_id = fields.BigIntField(null=True)
    """The ID of the self role of the guild."""

    shard_id = fields.BigIntField(null=True)
    """Returns the shard ID for this guild if applicable."""

    bot_nickname = fields.CharField(max_length=256, null=True)
    """The nickname of the bot in the guild."""

    bot_joined_at = fields.DatetimeField(null=True)
    """When the bot joined the guild."""

    chunked = fields.BooleanField(default=False, null=True)
    """Returns a boolean indicating if the guild is “chunked”.
    A chunked guild means that member_count is equal to the number of members stored in the internal members cache.
    If this value returns False, then you should request for offline members."""
    
    large = fields.BooleanField(default=False, null=True)
    """Indicates if the guild is a 'large'guild.
    A large guild is defined as having more than `large_threshold` count members, which for this library is set to the maximum of 250."""

    bot_in_guild = fields.BooleanField(default=False, null=True)
    """Whether the bot is in the guild or not."""

    @classmethod
    async def from_guild(cls, guild: discord.Guild, bot: Union[discord.Client, commands.Bot]):
        if not guild:
            return None
        assert guild

        # if not guild.approximate_member_count: # not fetched with with_counts=True
        #     guild = await bot.fetch_guild(guild.id, with_counts=True)
        
        old_instance = await cls.filter(guild_id=guild.id).first()
        if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
            await PastDiscordGuilds.from_db(old_instance)
        
        if guild.owner:
            user = await DiscordUsers.from_user(guild.owner, bot)
        elif guild.owner_id:
            user = await DiscordUsers.get_or_none(user_id=guild.owner_id)
        else:
            user = None
        instance, _ = await cls.update_or_create(
            guild_id=guild.id,
            defaults={
                'name': guild.name,
                'guild_created_at': guild.created_at,
                'guild_owner_id': guild.owner_id,
                'owner': user,

                'features': guild.features,
                'vanity_url': guild.vanity_url,
                'vanity_url_code': guild.vanity_url_code,

                'approximate_member_count': guild.approximate_member_count,
                'member_count': guild.member_count,
                'approximate_presence_count': guild.approximate_presence_count,

                'max_members': guild.max_members,
                'max_presences': guild.max_presences,
                'max_video_channel_users': guild.max_video_channel_users,
                'bitrate_limit': guild.bitrate_limit,
                'filesize_limit': guild.filesize_limit,
                'sticker_limit': guild.sticker_limit,
                'emoji_limit': guild.emoji_limit,

                'afk_timeout': guild.afk_timeout,
                'verification_level': guild.verification_level.value,
                'explicit_content_filter': guild.explicit_content_filter.value,
                'default_notifications': guild.default_notifications.value,
                'premium_tier': guild.premium_tier,
                'premium_subscription_count': guild.premium_subscription_count,
                'preferred_locale': guild.preferred_locale.value,
                'nsfw_level': guild.nsfw_level.value,
                'mfa_level': guild.mfa_level.value,
                'premium_progress_bar_enabled': guild.premium_progress_bar_enabled,
                'widget_enabled': guild.widget_enabled,
                'widget_channel_id': guild.widget_channel.id if guild.widget_channel else None,
                'default_role_id': guild.default_role.id,
                'premium_subscriber_role_id': guild.premium_subscriber_role.id if guild.premium_subscriber_role else None,
                
                'invited_paused_until': guild.invites_paused_until,
                'dms_paused_until': guild.dms_paused_until,
                
                'icon_url': guild.icon.url if guild.icon else None,
                'icon_bytes': await guild.icon.read() if guild.icon else None,
                'banner_url': guild.banner.url if guild.banner else None,
                'banner_bytes': await guild.banner.read() if guild.banner else None,
                'splash_url': guild.splash.url if guild.splash else None,
                'splash_bytes': await guild.splash.read() if guild.splash else None,
                'discovery_splash_url': guild.discovery_splash.url if guild.discovery_splash else None,
                'discovery_splash_bytes': await guild.discovery_splash.read() if guild.discovery_splash else None,
                'self_role_id': guild.self_role.id if guild.self_role else None,
                'shard_id': guild.shard_id,
                'bot_joined_at': guild.me.joined_at,
                'chunked': guild.chunked,
                'large': guild.large,
                'bot_in_guild': guild.me is not None
            }
        )

        if guild.channels:
            for channel in guild.channels:
                await DiscordChannels.from_channel(channel, bot=bot, guild=instance)

        if guild.roles:
            for role in guild.roles:
                await DiscordRoles.from_role(role, bot=bot, guild=instance)

        if guild.members:
            for member in guild.members:
                await DiscordMembers.from_member(member, bot=bot, guild=instance)

        return instance

    class Meta:
        table = "DiscordGuilds"

class PastDiscordGuilds(DiscordGuilds):
    """A table to store past guilds, or previous versions of guilds."""
    guild_id = fields.BigIntField()
    """The ID of the guild."""

    owner = fields.ForeignKeyField('my_app.DiscordUsers', related_name='past_owner', null=True)
    """The owner of the guild."""
    
    @classmethod
    async def from_db(cls, old: DiscordGuilds):
        await old.fetch_related('owner')
        return await cls.create(
            guild_id=old.guild_id,
            name=old.name,
            guild_created_at=old.guild_created_at,
            guild_owner_id=old.guild_owner_id,
            owner=old.owner,

            features=old.features,
            vanity_url=old.vanity_url,
            vanity_url_code=old.vanity_url_code,

            approximate_member_count=old.approximate_member_count,
            member_count=old.member_count,
            approximate_presence_count=old.approximate_presence_count,

            max_members=old.max_members,
            max_presences=old.max_presences,
            max_video_channel_users=old.max_video_channel_users,
            bitrate_limit=old.bitrate_limit,
            filesize_limit=old.filesize_limit,
            sticker_limit=old.sticker_limit,
            emoji_limit=old.emoji_limit,

            afk_timeout=old.afk_timeout,
            verification_level=old.verification_level,
            explicit_content_filter=old.explicit_content_filter,
            default_notifications=old.default_notifications,
            premium_tier=old.premium_tier,
            premium_subscription_count=old.premium_subscription_count,
            preferred_locale=old.preferred_locale,
            nsfw_level=old.nsfw_level,
            mfa_level=old.mfa_level,
            premium_progress_bar_enabled=old.premium_progress_bar_enabled,
            widget_enabled=old.widget_enabled,
            widget_channel_id=old.widget_channel_id,
            default_role_id=old.default_role_id,
            premium_subscriber_role_id=old.premium_subscriber_role_id,
            
            invited_paused_until=old.invited_paused_until,
            dms_paused_until=old.dms_paused_until,
            
            icon_url=old.icon_url,
            icon_bytes=old.icon_bytes,
            banner_url=old.banner_url,
            banner_bytes=old.banner_bytes,
            splash_url=old.splash_url,
            splash_bytes=old.splash_bytes,
            discovery_splash_url=old.discovery_splash_url,
            discovery_splash_bytes=old.discovery_splash_bytes,
            self_role_id=old.self_role_id,
            shard_id=old.shard_id,
            bot_joined_at=old.bot_joined_at,
            chunked=old.chunked,
            large=old.large,
            bot_in_guild=old.bot_in_guild
        )

    class Meta:
        table = "PastDiscordGuilds"

class DiscordUsers(Base):
    user_id = fields.BigIntField(unique=True)
    """The ID of the user."""

    name = fields.CharField(max_length=256)
    """The user's username."""

    discriminator = fields.CharField(max_length=4, null=True)
    """The user's discriminator. This is a legacy concept that is no longer used."""

    global_name = fields.CharField(max_length=256, null=True)
    """The user's global nickname, taking precedence over the username in display."""

    bot = fields.BooleanField(default=False)
    """Specifies if the user is a bot account."""

    system = fields.BooleanField(default=False)
    """Specifies if the user is a system user (i.e. represents Discord officially)."""

    dm_channel_id = fields.BigIntField(null=True)
    """Returns the channel associated with this user if it exists.
    If this returns None, you can create a DM channel by calling the create_dm() coroutine function."""

    accent_color = fields.IntField(null=True)
    """Returns the user's accent color, if applicable.
    A user's accent color is only shown if they do not have a banner. This will only be available if the user explicitly sets a color."""

    avatar_url = fields.CharField(max_length=1024, null=True)
    """The URL of the user's avatar."""

    avatar_bytes = fields.BinaryField(null=True)
    """The user's avatar, represented as bytes."""

    avatar_decoration_url = fields.CharField(max_length=1024, null=True)
    """The URL of the user's avatar decoration."""

    avatar_decoration_bytes = fields.BinaryField(null=True)
    """The user's avatar decoration, represented as bytes."""

    avatar_decoration_sku_id = fields.BigIntField(null=True)
    """Returns the SKU ID of the avatar decoration the user has.
    If the user has not set an avatar decoration, None is returned."""

    banner_url = fields.CharField(max_length=1024, null=True)
    """Returns the user's banner asset, if available.
    This information is only available via Client.fetch_user()."""

    banner_bytes = fields.BinaryField(null=True)
    """The user's banner, represented as bytes."""

    color = fields.IntField(null=True)
    """A property that returns a color denoting the rendered color for the user. This always returns Colour.default()."""

    user_created_at = fields.DatetimeField(null=True)
    """Returns the user's creation time in UTC.
    This is when the user's Discord account was created."""

    default_avatar_url = fields.CharField(max_length=1024, null=True)
    """The URL of the user's default avatar."""

    default_avatar_bytes = fields.BinaryField(null=True)
    """The user's default avatar, represented as bytes."""

    # display_avatar points to either avatar_url or default_avatar_url
    # display_name points to either global_name or name

    public_flags = fields.BigIntField(null=True)
    """The publicly available flags the user has."""

    @classmethod
    async def from_user(cls, user: Union[discord.User, discord.Member], bot: Union[discord.Client, commands.Bot]):
        if not user:
            return None
        assert user

        # if not user.dm_channel:
        #     await user.create_dm()
        old_instance = await cls.filter(user_id=user.id).first()
        if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
            await PastDiscordUsers.from_db(old_instance)

        instance, _ = await cls.update_or_create(
            user_id=user.id,
            defaults={
                'name': user.name,
                'discriminator': user.discriminator,
                'global_name': user.display_name,
                'bot': user.bot,
                'system': user.system,
                'dm_channel_id': getattr(getattr(user, 'dm_channel', None), 'id', None),
                'accent_color': user.accent_color,
                'avatar_url': user.avatar.url if user.avatar else None,
                'avatar_bytes': await user.avatar.read() if user.avatar else None,
                'avatar_decoration_url': user.avatar_decoration.url if user.avatar_decoration else None,
                'avatar_decoration_bytes': await user.avatar_decoration.read() if user.avatar_decoration else None,
                'avatar_decoration_sku_id': user.avatar_decoration_sku_id,
                'banner_url': user.banner.url if user.banner else None,
                'banner_bytes': await user.banner.read() if user.banner else None,
                'color': user.color.value,
                'user_created_at': user.created_at,
                'default_avatar_url': user.default_avatar.url if user.default_avatar else None,
                'default_avatar_bytes': await user.default_avatar.read() if user.default_avatar else None,
                'public_flags': user.public_flags.value
            }
        )

        return instance

    class Meta:
        table = "DiscordUsers"

class PastDiscordUsers(DiscordUsers):
    """A table to store past users, or previous versions of users."""
    user_id = fields.BigIntField()
    """The ID of the user."""

    @classmethod
    async def from_db(cls, old: DiscordUsers):
        return await cls.create(
            user_id=old.user_id,
            name=old.name,
            discriminator=old.discriminator,
            global_name=old.global_name,
            bot=old.bot,
            system=old.system,
            dm_channel_id=old.dm_channel_id,
            accent_color=old.accent_color,
            avatar_url=old.avatar_url,
            avatar_byes=old.avatar_bytes,
            avatar_decoration_url=old.avatar_decoration_url,
            avatar_decoration_bytes=old.avatar_decoration_bytes,
            avatar_decoration_sku_id=old.avatar_decoration_sku_id,
            banner_url=old.banner_url,
            banner_bytes=old.banner_bytes,
            color=old.color,
            user_created_at=old.user_created_at,
            default_avatar_url=old.default_avatar_url,
            default_avatar_bytes=old.default_avatar_bytes,
            public_flags=old.public_flags
        ) 
    class Meta:
        table = "PastDiscordUsers"

class DiscordMembers(Base):
    """A table to store members of a guild. All will have a relation to a guild."""

    guild = fields.ForeignKeyField('my_app.DiscordGuilds', related_name='guild')
    """The guild the member is in."""

    user = fields.ForeignKeyField('my_app.DiscordUsers', related_name='user')
    """The user who is a member of the guild."""

    nick = fields.CharField(max_length=256, null=True)
    """The guild specific nickname of the user. Takes precedence over the global name."""

    pending = fields.BooleanField(default=False)
    """Whether the member is pending member verification."""

    premium_since = fields.DatetimeField(null=True)
    """An aware datetime object that specifies the date and time in UTC when the member used their “Nitro boost” on the guild, if available. This could be None."""

    timed_out_until = fields.DatetimeField(null=True)
    """An aware datetime object that specifies the date and time in UTC that the member's time out will expire. This will be set to None if the user is not timed out."""

    raw_status = fields.CharField(max_length=512, null=True)
    """The member's overall status as a string value."""

    status = fields.CharField(max_length=512, null=True)
    """The member's overall status. If the value is unknown, then it will be a str instead."""

    mobile_status = fields.CharField(max_length=512, null=True)
    """The member's status on a mobile device, if applicable."""

    desktop_status = fields.CharField(max_length=512, null=True)
    """The member's status on a desktop device, if applicable."""

    web_status = fields.CharField(max_length=512, null=True)
    """The member's status on a web device, if applicable."""

    color = fields.CharField(max_length=512, null=True)
    """A property that returns a colour denoting the rendered colour for the member. If the default colour is the one rendered then an instance of Colour.default() is returned."""

    guild_avatar_url = fields.CharField(max_length=1024, null=True)
    """Returns a URL for the guild avatar the member has. If unavailable, None is returned."""

    guild_avatar_bytes = fields.BinaryField(null=True)
    """The guild avatar, represented as bytes."""

    guild_permissions = fields.BigIntField(null=True)
    """The guild permissions the member has."""

    @classmethod
    async def from_member(cls, member: discord.Member, bot: Union[discord.Client, commands.Bot], guild: Optional[DiscordGuilds]=None):
        if not member:
            return None
        assert member

        if not guild:
            guild = await DiscordGuilds.from_guild(member.guild, bot)

        old_instance = await cls.filter(guild=guild, user__user_id=member.id).first()
        if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
            await PastDiscordMembers.from_db(old_instance)
        
        if not await DiscordUsers.filter(user_id=member.id).exists():
            user = await DiscordUsers.from_user(member, bot)
        else:
            user = await DiscordUsers.get(user_id=member.id)

        instance, _ = await cls.update_or_create(
            guild=guild,
            user=user,
            defaults={
                'nick': member.nick,
                'pending': member.pending,
                'premium_since': member.premium_since,
                'timed_out_until': member.timed_out_until,
                'raw_status': str(member.raw_status) if member.raw_status else None,
                'status': str(member.status.value) if member.status else None,
                'mobile_status': str(member.mobile_status.value) if member.mobile_status else None,
                'desktop_status': str(member.desktop_status.value) if member.desktop_status else None,
                'web_status': str(member.web_status.value) if member.web_status else None,
                'color': member.color.value,
                'guild_avatar_url': member.guild_avatar.url if member.guild_avatar else None,
                'guild_avatar_bytes': await member.guild_avatar.read() if member.guild_avatar else None,
                'guild_permissions': member.guild_permissions.value
            }
        )

        return instance

    class Meta:
        table = "DiscordMembers"

class PastDiscordMembers(DiscordMembers):
    """A table to store past members, or previous versions of members."""
    guild = fields.BigIntField()
    """The ID of the guild."""

    user = fields.BigIntField()
    """The ID of the user."""

    @classmethod
    async def from_db(cls, old: DiscordMembers):
        await old.fetch_related('guild', 'user')
        return await cls.create(
            guild=old.guild.guild_id,
            user=old.user.user_id,
            nick=old.nick,
            pending=old.pending,
            premium_since=old.premium_since,
            timed_out_until=old.timed_out_until,
            raw_status=old.raw_status,
            status=old.status,
            mobile_status=old.mobile_status,
            desktop_status=old.desktop_status,
            web_status=old.web_status,
            color=old.color,
            guild_avatar_url=old.guild_avatar_url,
            guild_avatar_bytes=old.guild_avatar_bytes,
            guild_permissions=old.guild_permissions
        )

    class Meta:
        table = "PastDiscordMembers"

class DiscordChannels(Base):
    """Represents a Discord channel. This could be a guild channel."""

    guild = fields.ForeignKeyField('my_app.DiscordGuilds', related_name='channels', null=True)
    """The guild the channel is in."""

    channel_id = fields.BigIntField(unique=True)
    """The ID of the channel."""

    name = fields.CharField(max_length=256, null=True)
    """The name of the channel."""

    jump_url = fields.CharField(max_length=1024, null=True)
    """The URL that leads to the channel."""

    channel_created_at = fields.DatetimeField(null=True)
    """The channel's creation time in UTC."""

    category_id = fields.BigIntField(null=True)
    """The ID of the category the channel is in."""

    permissions_synced = fields.BooleanField(default=False)
    """Specifies if the channel's permissions are synced with the category's permissions. If there is no category, this will be False."""

    type = fields.IntField()
    """The type of the channel. This can be a text, voice, category, private, group, category, news, stage_voice, news_thread, public_thread, private_thread, forum, media."""

    position = fields.IntField(null=True)
    """The position of the channel in the channel list. This is a number that starts at 0.
    Available for:
    Text Channels
    Forum Channels
    Voice Channels
    """

    topic = fields.CharField(max_length=4096, null=True)
    """The channel's topic.
    Available for:
    Text Channels
    Forum Channels (called guildelines in UI)
    Stage Channels
    """

    last_message_id = fields.BigIntField(null=True)
    """The last message ID of the message sent to this channel. It may not point to an existing or valid message.
    Available for:
    Text Channels
    Forum Channels
    Threads
    Voice Channels
    Stage Channels
    """

    slowmode_delay = fields.IntField(null=True)
    """The slowmode delay for the channel in seconds.
    Available for:
    Text Channels
    Forum Channels
    Threads
    Voice Channels
    Stage Channels
    """

    nsfw = fields.BooleanField(default=False)
    """If the channel is marked as “not safe for work” or “age restricted”.
    Available for:
    Text Channels
    Forum Channels
    Voice Channels
    Stage Channels
    """

    default_auto_archive_duration = fields.IntField(null=True)
    """The default auto archive duration in minutes for threads created in this channel.
    Available for:
    Text Channels
    Forum Channels
    """

    default_thread_slowmode_delay = fields.IntField(null=True)
    """The default slowmode delay in seconds for threads created in this channel.
    Available for:
    Text Channels
    Forum Channels
    """
    
    default_reaction_emoji = fields.CharField(max_length=256, null=True)
    """The default reaction emoji for threads created in this forum to show in the add reaction button.
    Available for:
    Forum Channels
    """

    default_layout = fields.IntField(null=True)
    """The default layout for threads created in this forum.
    Available for:
    Forum Channels
    """

    default_sort_order = fields.IntField(null=True)
    """The default sort order for threads created in this forum.
    Available for:
    Forum Channels
    """

    flags = fields.BigIntField(null=True)
    """The channel's flags.
    Available for:
    Forum Channels
    Threads
    """

    parent_id = fields.BigIntField(null=True)
    """The parent TextChannel or ForumChannel ID this thread belongs to.
    Available for:
    Threads
    """

    owner_id = fields.BigIntField(null=True)
    """The ID of the user who owns this channel.
    Available for:
    Threads
    """

    message_count = fields.BigIntField(null=True)
    """An approximate number of messages in this thread.
    Available for:
    Threads
    """

    member_count = fields.BigIntField(null=True)
    """An approximate number of members in this thread. This caps at 50.
    Available for:
    Threads
    """

    archived = fields.BooleanField(default=False)
    """Specifies if the thread is archived.
    Available for:
    Threads
    """

    invitable = fields.BooleanField(default=False)
    """Specifies if the thread is invitable.
    Available for:
    Threads
    """

    archiver_id = fields.BigIntField(null=True)
    """The user's ID that archived this thread.
    Due to an API change, the archiver_id is always None and must be obtained from the audio log."""

    auto_archive_duration = fields.IntField(null=True)
    """The duration in minutes until the thread is automatically hidden from the channel list. Usually a value of 60, 1440, 4320 and 10080."""

    archive_timestamp = fields.DatetimeField(null=True)
    """An aware timestamp of when the thread's archived status was last updated in UTC."""

    starter_message_id = fields.BigIntField(null=True)
    """Returns the thread starter message from the cache. The message might not be cached, valid, or point to an existing message. Note that the thread starter message ID is the same ID as the thread.
    Available for:
    Threads
    """

    bitrate = fields.BigIntField(null=True)
    """The channel's preferred audio bitrate in bits per second.
    Available for:
    Voice Channels
    Stage Channels
    """

    rtc_region = fields.CharField(max_length=256, null=True)
    """The region for the voice channel's voice communication. A value of None indicates automatic voice region detection.
    Available for:
    Voice Channels
    Stage Channels
    """

    user_limit = fields.BigIntField(null=True)
    """The channel's limit for number of members that can be in a voice channel.
    Available for:
    Voice Channels
    Stage Channels
    """

    video_quality_mode = fields.IntField(null=True)
    """The camera video quality for the voice channel's participants.
    Available for:
    Voice Channels
    Stage Channels
    """

    icon_url = fields.CharField(max_length=1024, null=True)
    """Returns the channel's icon asset if available.
    Available for:
    Group DMs
    """

    icon_bytes = fields.BinaryField(null=True)
    """The channel's icon, represented as bytes.
    Available for:
    Group DMs
    """

    @classmethod
    async def from_channel(cls, channel: Union[discord.abc.GuildChannel, discord.abc.Snowflake], bot: Union[discord.Client, commands.Bot], guild: Optional[DiscordGuilds]=None):
        if not channel:
            return
        assert channel

        if not guild and isinstance(channel, discord.abc.GuildChannel):
            guild = await DiscordGuilds.from_guild(channel.guild, bot)

        old_instance = await cls.filter(channel_id=channel.id).first()
        if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
            await PastDiscordChannels.from_db(old_instance)

        instance, _ = await cls.update_or_create(
            guild=guild,
            channel_id=channel.id,
            defaults={
                'name': getattr(channel, 'name', None),
                'jump_url': getattr(channel, 'jump_url', None),
                'channel_created_at': channel.created_at, # type: ignore
                'category_id': getattr(channel, 'category_id', None),
                'permissions_synced': getattr(channel, 'permissions_synced', False),
                'type': getattr(channel, 'type').value, # type: ignore
                'position': getattr(channel, 'position', None),
                'topic': getattr(channel, 'topic', None),
                'last_message_id': getattr(channel, 'last_message_id', None),
                'slowmode_delay': getattr(channel, 'slowmode_delay', None),
                'nsfw': getattr(channel, 'nsfw', False),
                'default_auto_archive_duration': getattr(channel, 'default_auto_archive_duration', None),
                'default_thread_slowmode_delay': getattr(channel, 'default_thread_slowmode_delay', None),
                'default_reaction_emoji': str(getattr(channel, 'default_reaction_emoji', None)) if getattr(channel, 'default_reaction_emoji', None) else None,
                'default_layout': getattr(getattr(channel, 'default_layout', None), 'value', None) if isinstance(channel, (discord.ForumChannel,)) else None,
                'default_sort_order': getattr(getattr(channel, 'default_sort_order', None), 'value', None) if isinstance(channel, (discord.ForumChannel,)) else None,
                'flags': getattr(getattr(channel, 'flags', None), 'flags', None) if isinstance(channel, (discord.ForumChannel, discord.Thread)) else None,
                'parent_id': getattr(channel, 'parent_id', None),
                'owner_id': getattr(channel, 'owner_id', None),
                'message_count': getattr(channel, 'message_count', None),
                'member_count': getattr(channel, 'member_count', None),
                'archived': getattr(channel, 'archived', False),
                'invitable': getattr(channel, 'invitable', False),
                'archiver_id': getattr(channel, 'archiver_id', None),
                'auto_archive_duration': getattr(channel, 'auto_archive_duration', None),
                'archive_timestamp': getattr(channel, 'archive_timestamp', None),
                'starter_message_id': getattr(getattr(channel, 'starter_message',None), 'id', None),
                'bitrate': getattr(channel, 'bitrate', None),
                'rtc_region': getattr(channel, 'rtc_region', None),
                'user_limit': getattr(channel, 'user_limit', None),
                'video_quality_mode': getattr(getattr(channel, 'video_quality_mode', None), 'value', None) if isinstance(channel, (discord.VoiceChannel, discord.StageChannel)) else None,
            }
        )

        return instance
    
    class Meta:
        table = "DiscordChannels"

class PastDiscordChannels(DiscordChannels):
    guild = fields.ForeignKeyField('my_app.DiscordGuilds', related_name='past_channels', null=True)

    channel_id = fields.BigIntField()

    @classmethod
    async def from_db(cls, old: DiscordChannels):
        await old.fetch_related('guild')

        try:
            return await cls.create(
            guild=old.guild,
            channel_id=old.channel_id,
            name=old.name,
            jump_url=old.jump_url,
            channel_created_at=old.channel_created_at,
            category_id=old.category_id,
            permissions_synced=old.permissions_synced,
            type=old.type,
            position=old.position,
            topic=old.topic,
            last_message_id=old.last_message_id,
            slowmode_delay=old.slowmode_delay,
            nsfw=old.nsfw,
            default_auto_archive_duration=old.default_auto_archive_duration,
            default_thread_slowmode_delay=old.default_thread_slowmode_delay,
            default_reaction_emoji=old.default_reaction_emoji,
            default_layout=old.default_layout,
            default_sort_order=old.default_sort_order,
            flags=old.flags,
            parent_id=old.parent_id,
            owner_id=old.owner_id,
            message_count=old.message_count,
            member_count=old.member_count,
            archived=old.archived,
            invitable=old.invitable,
            archiver_id=old.archiver_id,
            auto_archive_duration=old.auto_archive_duration,
            archive_timestamp=old.archive_timestamp,
            starter_message_id=old.starter_message_id,
            bitrate=old.bitrate,
            rtc_region=old.rtc_region,
            user_limit=old.user_limit,
            video_quality_mode=old.video_quality_mode
            )
        except Exception as e:

            guild = old.guild
            guild_id = guild.guild_id
            print(e)

    
    class Meta:
        table = "PastDiscordChannels"

class DiscordRoles(Base):
    """A table to store roles in a guild."""

    role_id = fields.BigIntField(unique=True)
    """The ID for the role."""

    name = fields.CharField(max_length=256)
    """The name of the role."""

    guild = fields.ForeignKeyField('my_app.DiscordGuilds', related_name='roles')
    """The guild the role belongs to."""

    role_created_at = fields.DatetimeField()
    """Returns the role's creation time in UTC."""

    hoist = fields.BooleanField(default=False)
    """Indicates if the role will be displayed separately from other members."""

    position = fields.IntField()
    """The position of the role. This number is usually positive. The bottom role has a position of 0.
    Multiple roles can have the same position number. As a consequence of this, comparing via role position is prone to subtle bugs if checking for role hierarchy. The recommended and correct way to compare for roles in the hierarchy is using the comparison operators on the role objects themselves."""

    unicode_emoji = fields.CharField(max_length=256, null=True)
    """The role's unicode emoji, if available.
    If icon is not None, it is displayed as role icon instead of the unicode emoji under this attribute.
    If you want the icon that a role has displayed, consider using display_icon."""

    managed = fields.BooleanField(default=False)
    """Indicates if the role is managed by the guild through some form of integrations such as Twitch."""

    mentionable = fields.BooleanField(default=False)
    """Indicates if the role can be mentioned by users."""

    #tags = 

    is_default = fields.BooleanField(default=False)
    """Checks if the role is the default role."""

    is_bot_managed = fields.BooleanField(default=False)
    """Whether the role is associated with a bot."""

    is_premium_subscriber = fields.BooleanField(default=False)
    """ Whether the role is the premium subscriber, AKA “boost”, role for the guild."""

    permissions = fields.BigIntField()
    """Returns the role's permissions."""

    icon_url = fields.CharField(max_length=1024, null=True)
    """Returns the role's icon asset if available."""

    icon_bytes = fields.BinaryField(null=True)
    """The role's icon, represented as bytes."""

    flags = fields.BigIntField(null=True)
    """Returns the role's flags."""

    @classmethod
    async def from_role(cls, role: discord.Role, bot: Union[discord.Client, commands.Bot], guild: Optional[DiscordGuilds]=None):
        if not role:
            return None
        
        if not guild:
            guild = await DiscordGuilds.from_guild(role.guild, bot)
        
        old_instance = await cls.filter(name=role.name, guild=guild).first()
        if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
            await PastDiscordRoles.from_db(old_instance)
        
        instance, _ = await cls.update_or_create(
            role_id=role.id,
            guild=guild,
            defaults={
                'name': role.name,
                'role_created_at': role.created_at,
                'hoist': role.hoist,
                'position': role.position,
                'unicode_emoji': role.unicode_emoji,
                'managed': role.managed,
                'mentionable': role.mentionable,
                'is_default': role.is_default(),
                'is_bot_managed': role.is_bot_managed(),
                'is_premium_subscriber': role.is_premium_subscriber(),
                'permissions': role.permissions.value,
                'icon_url': role.icon.url if role.icon else None,
                'icon_bytes': await role.icon.read() if role.icon else None,
                'flags': role.flags.value
            }
        )


        return instance

    class Meta:
        table = "DiscordRoles"

class PastDiscordRoles(DiscordRoles):
    """A table to store past roles, or previous versions of roles."""
    
    role_id = fields.BigIntField()
    """The ID for the role."""

    guild = fields.ForeignKeyField('my_app.DiscordGuilds', related_name='past_roles', null=True)
    """The guild the role belongs to."""

    @classmethod
    async def from_db(cls, old: DiscordRoles):
        await old.fetch_related('guild')
        return await cls.create(
            role_id=old.role_id,
            guild=old.guild,
            name=old.name,
            role_created_at=old.role_created_at,
            hoist=old.hoist,
            position=old.position,
            unicode_emoji=old.unicode_emoji,
            managed=old.managed,
            mentionable=old.mentionable,
            is_default=old.is_default,
            is_bot_managed=old.is_bot_managed,
            is_premium_subscriber=old.is_premium_subscriber,
            permissions=old.permissions,
            icon_url=old.icon_url,
            icon_bytes=old.icon_bytes,
            flags=old.flags
        )

    class Meta:
        table = "PastDiscordRoles"

class DiscordMessages(Base):
    """Represents a Discord message."""

    guild = fields.ForeignKeyField('my_app.DiscordGuilds', related_name='messages', null=True)
    """The guild the message is in."""

    channel = fields.ForeignKeyField('my_app.DiscordChannels', related_name='messages')
    """The TextChannel or Thread that the message was sent from. Could be a DMChannel or GroupChannel if it's a private message."""

    tts = fields.BooleanField(default=False)
    """Specifies if the message was done with text-to-speech. This can only be accurately received in on_message() due to a discord limitation."""

    type = fields.IntField()
    """The type of message. In most cases this should not be checked, but it is helpful in cases where it might be a system message for system_content."""

    author = fields.ForeignKeyField('my_app.DiscordUsers', related_name='author')
    """The author of the message."""

    content = fields.TextField()
    """The actual contents of the message. If Intents.message_content is not enabled this will always be an empty string unless the bot is mentioned or the message is a direct message."""

    nonce = fields.CharField(max_length=256, null=True)
    """The value used by the discord guild and the client to verify that the message is successfully sent. This is not stored long term within Discord's servers and is only used ephemerally."""

    embeds = fields.JSONField(null=True)
    """A list of embeds the message has. If Intents.message_content is not enabled this will always be an empty list unless the bot is mentioned or the message is a direct message."""

    reference = fields.ForeignKeyField('my_app.DiscordMessageReference', related_name='reference', null=True)
    """The message that this message references. This is only applicable to messages of type MessageType.pins_add, crossposted messages created by a followed channel integration, or message replies."""

    mention_everyone = fields.BooleanField(default=False)
    """Specifies if the message mentions everyone.
    This does not check if the @everyone or the @here text is in the message itself. Rather this boolean indicates if either the @everyone or the @here text is in the message and it did end up mentioning."""

    webhook_id = fields.BigIntField(null=True)
    """If this message was sent by a webhook, then this is the webhook ID's that sent this message."""

    attachments = fields.ManyToManyField('my_app.DiscordAttachments', related_name='attachments', null=True)
    """A list of attachments given to a message. If Intents.message_content is not enabled this will always be an empty list unless the bot is mentioned or the message is a direct message."""

    pinned = fields.BooleanField(default=False)
    """Specifies if the message is pinned."""

    flags = fields.BigIntField(null=True)
    """The message's flags."""

    activity = fields.JSONField(null=True)
    """The activity associated with this message. Sent with Rich-Presence related messages that for example, request joining, spectating, or listening to or with another member.

    It is a dictionary with the following optional keys:

    type: An integer denoting the type of message activity being requested.

    party_id: The party ID associated with the party.
    """
    
    application_id = fields.BigIntField(null=True)
    """The application ID of the application that created this message if this message was sent by an application-owned webhook or an interaction."""

    position = fields.BigIntField(null=True)
    """A generally increasing integer with potentially gaps or duplicates that represents the approximate position of the message in a thread."""

    @classmethod
    async def from_message(cls, message: discord.Message, bot: Union[discord.Client, commands.Bot]):
        if not message:
            return None
        assert message

        if not message.guild:
            guild = None
        else:
            guild = await DiscordGuilds.from_guild(message.guild, bot)

        channel = await DiscordChannels.from_channel(message.channel, bot, guild)

        old_instance = await cls.filter(channel=channel, author=await DiscordUsers.from_user(message.author, bot)).first()
        if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
            await PastDiscordMessages.from_db(old_instance)

        if not DiscordUsers.filter(user_id=message.author.id).first():
            user = await DiscordUsers.from_user(message.author, bot)
        else:
            user = await DiscordUsers.get(user_id=message.author.id)
        instance, _ = await cls.update_or_create(
            guild=guild,
            channel=channel,
            author=user,
            defaults={
                'tts': message.tts,
                'type': message.type.value,
                'content': message.content,
                'nonce': message.nonce,
                'embeds': [embed.to_dict() for embed in message.embeds],
                'reference': await DiscordMessageReference.from_message_reference(message.reference) if message.reference else None,
                'mention_everyone': message.mention_everyone,
                'webhook_id': message.webhook_id,
                'pinned': message.pinned,
                'flags': message.flags.value,
                'activity': message.activity,
                'application_id': message.application_id,
                'position': message.position
            }
        )
        await instance.attachments.add(*await DiscordAttachments.from_message(message))
        return instance

    class Meta:
        table = "DiscordMessages"

class PastDiscordMessages(DiscordMessages):
    guild = fields.BigIntField(null=True)
    channel = fields.BigIntField()
    author = fields.BigIntField()

    reference = fields.ForeignKeyField('my_app.DiscordMessageReference', related_name='past_reference', null=True)

    attachments = fields.ManyToManyField('my_app.DiscordAttachments', related_name='past_attachments', null=True)

    @classmethod
    async def from_db(cls, old: DiscordMessages):
        await old.fetch_related('guild', 'channel', 'author', 'reference', 'attachments')
        instance = await cls.create(
            guild=getattr(old.guild, 'guild_id', None),
            channel=getattr(old.channel, 'channel_id', None),
            author=getattr(old.author, 'user_id', None),
            tts=old.tts,
            type=old.type,
            content=old.content,
            nonce=old.nonce,
            embeds=old.embeds,
            reference=old.reference,
            mention_everyone=old.mention_everyone,
            webhook_id=old.webhook_id,
            pinned=old.pinned,
            flags=old.flags,
            activity=old.activity,
            application_id=old.application_id,
            position=old.position
        )
    
        if old.attachments:
            await instance.attachments.add(*old.attachments)
        
        return instance

    class Meta:
        table = "PastDiscordMessages"

class DiscordMessageReference(Base):
    """Represents a reference to a message."""

    message_id = fields.BigIntField(null=True)
    """The ID of the message being referenced."""

    channel_id = fields.BigIntField()
    """The ID of the channel the message is in."""

    guild_id = fields.BigIntField(null=True)
    """The ID of the guild the message is in."""

    fail_if_not_exists = fields.BooleanField(default=True)
    """Specifies if the message reference should fail if the message being referenced does not exist."""

    jump_url = fields.CharField(max_length=1024, null=True)
    """The URL that leads to the message being referenced."""

    @classmethod
    async def from_message_reference(cls, reference: discord.MessageReference):
        if not reference:
            return None
        assert reference

        old_instance = await cls.filter(message_id=reference.message_id).first()
        if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
            await PastDiscordMessageReference.from_db(old_instance)

        instance, _ = await cls.update_or_create(
            message_id=reference.message_id,
            defaults={
                'channel_id': reference.channel_id,
                'guild_id': reference.guild_id,
                'fail_if_not_exists': reference.fail_if_not_exists
            }
        )

        return instance

    class Meta:
        table = "DiscordMessageReference"

class PastDiscordMessageReference(DiscordMessageReference):
    message_id = fields.BigIntField(null=True)

    @classmethod
    async def from_db(cls, old: DiscordMessageReference):
        return await cls.create(
            message_id=old.message_id,
            channel_id=old.channel_id,
            guild_id=old.guild_id,
            fail_if_not_exists=old.fail_if_not_exists
        )

    class Meta:
        table = "PastDiscordMessageReference"

class DiscordAttachments(Base):
    """Table to store attachments of a message."""

    attachment_id = fields.BigIntField(unique=True)
    """The ID of the attachment."""

    message_id = fields.BigIntField(null=True)
    """The related message to this attachment, if applicable."""

    bytes = fields.BinaryField(null=True)
    """The bytes of the attachment."""

    size = fields.BigIntField()
    """The size of the attachment in bytes."""

    height = fields.IntField(null=True)
    """The height of the attachment in pixels. Only applicable to images and videos."""

    width = fields.IntField(null=True)
    """The width of the attachment in pixels. Only applicable to images and videos."""

    filename = fields.CharField(max_length=256)
    """The filename of the attachment."""

    url = fields.CharField(max_length=1024)
    """The attachment URL. If the message this attachment was attached to is deleted, then this will 404."""

    proxy_url = fields.CharField(max_length=1024)
    """The proxy URL. This is a cached version of the url in the case of images. When the message is deleted, this URL might be valid for a few minutes or not valid at all."""

    content_type = fields.CharField(max_length=256)
    """The attachment's media type"""

    description = fields.CharField(max_length=1024, null=True)
    """The attachment's description. Only applicable to images."""

    ephemeral = fields.BooleanField(default=False)
    """Specifies if the attachment is ephemeral."""

    duration = fields.FloatField(null=True)
    """The duration of the audio file in seconds. Returns None if it's not a voice message."""

    waveform = fields.BinaryField(null=True)
    """The waveform (amplitudes) of the audio in bytes. Returns None if it's not a voice message."""

    flags = fields.BigIntField(null=True)
    """The attachment's flags."""

    @classmethod
    async def from_message(cls, message: discord.Message):
        if not message:
            return None
        assert message

        instances = []

        for attachment in message.attachments:
            old_instance = await cls.filter(attachment_id=attachment.id).first()
            if old_instance and datetime.datetime.now(datetime.timezone.utc) -  getattr(old_instance, 'updated_at', datetime.datetime.now(datetime.timezone.utc)) > datetime.timedelta(hours=6):
                await PastDiscordAttachments.from_db(old_instance)

            instance, _ = await cls.update_or_create(
                attachment_id=attachment.id,
                defaults={
                    'bytes': await attachment.read(),
                    'message_id': message.id,
                    'size': attachment.size,
                    'height': attachment.height,
                    'width': attachment.width,
                    'filename': attachment.filename,
                    'url': attachment.url,
                    'proxy_url': attachment.proxy_url,
                    'content_type': attachment.content_type,
                    'description': attachment.description,
                    'ephemeral': attachment.ephemeral,
                    'duration': attachment.duration,
                    'waveform': attachment.waveform,
                    #'flags': attachment.flags.value if hasattr(attachment, 'flags') else None,
                }
            )

            instances.append(instance)

        return instances

    class Meta:
        table = "DiscordAttachments"

class PastDiscordAttachments(DiscordAttachments):
    attachment_id = fields.BigIntField()

    @classmethod
    async def from_db(cls, old: DiscordAttachments):
        return await cls.create(
            attachment_id=old.attachment_id,
            bytes=old.bytes,
            message_id=old.message_id,
            size=old.size,
            height=old.height,
            width=old.width,
            filename=old.filename,
            url=old.url,
            proxy_url=old.proxy_url,
            content_type=old.content_type,
            description=old.description,
            ephemeral=old.ephemeral,
            duration=old.duration,
            waveform=old.waveform,
            flags=old.flags
        )

    class Meta:
        table = "PastDiscordAttachments"


async def setup(*args):
    env = environ.Env(
        PROD=(bool, False)
    )

    PROD = env("PROD")
    if PROD:
        await Tortoise.init(config_file="db.yml")
    else:
        await Tortoise.init(config_file="db_beta.yml")
    await Tortoise.generate_schemas()
