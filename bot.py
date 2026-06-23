import os
import json
import discord
from discord.ext import commands

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")) as f:
    CONFIG = json.load(f)

PREFIX = CONFIG.get("prefix", ".")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.moderation = True

INITIAL_EXTENSIONS = [
    "whitelist",
    "sin",
    "moderation",
    "antinuke",
    "antimod",
    "boost",
    "application",
    "logging_cog",
    "welcome",
]


class SinBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.config = CONFIG

    async def setup_hook(self):
        for ext in INITIAL_EXTENSIONS:
            await self.load_extension(ext)


bot = SinBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Prefix: {PREFIX}")
    try:
        synced_guilds = len(bot.guilds)
        print(f"Connected to {synced_guilds} guild(s).")
    except Exception:
        pass

    # Try to keep the bot's actual Discord username in sync with config.json.
    # Discord rate-limits username changes (roughly 2/hour), so this is wrapped
    # in a try/except and will simply no-op if it's been changed too recently.
    desired_name = CONFIG.get("bot_name")
    if desired_name and bot.user and bot.user.name != desired_name:
        try:
            await bot.user.edit(username=desired_name)
            print(f"Renamed bot to {desired_name}")
        except discord.HTTPException as e:
            print(f"Could not rename bot (rate-limited or invalid name): {e}")

    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}sin | All-in-one bot"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(str(error) if str(error) else "❌ You can't use this command.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ I'm missing permissions needed to do that.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`. Use `{PREFIX}sin` for help.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.send(f"❌ An error occurred: {error}")
        print(f"Unhandled command error: {error!r}")


def main():
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN environment variable is not set. "
            "Set it in your .env file (local) or in Railway's Variables tab."
        )
    bot.run(token)


if __name__ == "__main__":
    main()
