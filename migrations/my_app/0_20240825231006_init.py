from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "Blacklist" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "offender_id" BIGINT NOT NULL,
    "offender_name" VARCHAR(100),
    "reason" VARCHAR(255),
    "timestamp" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "CommandInvocations" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "transaction_id" UUID,
    "command_id" BIGINT NOT NULL,
    "prefix" VARCHAR(25),
    "is_slash" BOOL NOT NULL  DEFAULT False,
    "user_id" BIGINT NOT NULL,
    "guild_id" BIGINT,
    "channel_id" BIGINT,
    "command" VARCHAR(100) NOT NULL,
    "args" JSONB NOT NULL,
    "kwargs" JSONB NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL,
    "completed" BOOL,
    "completion_timestamp" TIMESTAMPTZ,
    "error" VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS "Commands" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "guild_id" BIGINT,
    "channel_id" BIGINT,
    "author_id" BIGINT NOT NULL,
    "used" TIMESTAMPTZ NOT NULL,
    "uses" BIGINT NOT NULL  DEFAULT 1,
    "prefix" VARCHAR(23) NOT NULL,
    "command" VARCHAR(100) NOT NULL,
    "failed" BOOL NOT NULL  DEFAULT False,
    "app_command" BOOL NOT NULL  DEFAULT False,
    "args" JSONB,
    "kwargs" JSONB
);
CREATE TABLE IF NOT EXISTS "ReportedErrors" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "error_id" UUID NOT NULL,
    "user_id" BIGINT NOT NULL,
    "forum_id" BIGINT NOT NULL,
    "forum_post_id" BIGINT NOT NULL,
    "forum_initial_message_id" BIGINT NOT NULL,
    "error_message" TEXT,
    "resolved" BOOL NOT NULL  DEFAULT False
);
COMMENT ON TABLE "ReportedErrors" IS 'Errors Reported to my private forum via that menu thing.';
CREATE TABLE IF NOT EXISTS "Settings" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_id" BIGINT NOT NULL UNIQUE,
    "username" VARCHAR(100) NOT NULL,
    "preferred_platform" VARCHAR(5) NOT NULL  DEFAULT 'N/A',
    "show_on_leaderboard" BOOL NOT NULL  DEFAULT True,
    "prefix" VARCHAR(5) NOT NULL  DEFAULT '!',
    "use_custom_prefix" BOOL NOT NULL  DEFAULT False,
    "show_prefix_command_tips" BOOL NOT NULL  DEFAULT True,
    "language" VARCHAR(5) NOT NULL  DEFAULT 'en',
    "timezone" VARCHAR(50) NOT NULL  DEFAULT 'UTC',
    "color" VARCHAR(7) NOT NULL  DEFAULT '#7289DA'
);
CREATE TABLE IF NOT EXISTS "SettingsInfo" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "description" VARCHAR(100) NOT NULL,
    "valuetype" VARCHAR(100) NOT NULL,
    "emoji" VARCHAR(100),
    "min_value" INT,
    "max_value" INT,
    "active" BOOL NOT NULL  DEFAULT True
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
