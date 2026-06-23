import discord
import json
import os
from discord.ext import commands, tasks
from datetime import datetime, timezone

# Shared local data file configuration paths
SETTINGS_FILE = "guild_settings.json"
MESSAGE_COUNTS_FILE = "message_counts.json"

def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def get_guild(data, guild_id):
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {}
    return data[gid]


def get_message_counts():
    if not os.path.exists(MESSAGE_COUNTS_FILE):
        return {}
    try:
        with open(MESSAGE_COUNTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


class Application(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_eligibility.start()

    def cog_unload(self):
        self.check_eligibility.cancel()

    @commands.group(name="application", invoke_without_command=True)
    async def application(self, ctx):
        await ctx.send(f"Use `{ctx.prefix}application role set @role`.")

    @application.group(name="role", invoke_without_command=True)
    async def application_role(self, ctx):
        await ctx.send(f"Use `{ctx.prefix}application role set @role`.")

    @application_role.command(name="set")
    @commands.has_permissions(administrator=True)
    async def application_role_set(self, ctx, role: discord.Role):
        data = get_settings()
        g = get_guild(data, ctx.guild.id)
        g["application_role"] = role.id
        save_settings(data)
        await ctx.send(
            f"✅ {role.mention} will now automatically be given to members who have been in the "
            f"server for **{self.bot.config.get('application_required_days', 30)}+ days** and have "
            f"sent **{self.bot.config.get('application_required_messages', 500)}+ messages**.\n"
            f"This is checked automatically every hour."
        )

    @tasks.loop(hours=1)
    async def check_eligibility(self):
        required_days = self.bot.config.get("application_required_days", 30)
        required_messages = self.bot.config.get("application_required_messages", 500)
        data = get_settings()
        counts = get_message_counts()

        for guild in self.bot.guilds:
            g = get_guild(data, guild.id)
            role_id = g.get("application_role")
            if not role_id:
                continue
            role = guild.get_role(int(role_id))
            if not role:
                continue

            guild_counts = counts.get(str(guild.id), {})
            now = datetime.now(timezone.utc)

            for member in guild.members:
                if member.bot or role in member.roles:
                    continue
                if not member.joined_at:
                    continue
                days_in_server = (now - member.joined_at).days
                msg_count = guild_counts.get(str(member.id), 0)
                if days_in_server >= required_days and msg_count >= required_messages:
                    try:
                        await member.add_roles(role, reason="Met application requirements (age + message count)")
                    except (discord.Forbidden, discord.HTTPException):
                        continue

        save_settings(data)

    @check_eligibility.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Application(bot))
