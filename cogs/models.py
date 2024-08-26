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
