import discord
import json
import os
from discord.ext import commands

# Shared local data file configuration paths
SETTINGS_FILE = "guild_settings.json"
BOOST_KEYS_FILE = "boost_keys.json"

COMMAND_INFO = {
    "ban": "Bans a member from the server.",
    "unban": "Unbans a user by ID.",
    "mute": "Times out (mutes) a member for a given duration (e.g. 10m, 2h, 1d).",
    "timeout": "Alias of mute — times out a member.",
    "unmute": "Removes an active timeout from a member.",
    "role add": "Gives a role to a member.",
    "role remove": "Removes a role from a member.",
    "promote": "Promotes a member by giving them a role.",
    "demote": "Demotes a member by removing a role.",
    "antinuke": "Shows current antinuke status.",
    "antinuke enable": "Turns antinuke protection ON for this server.",
    "antinuke disable": "Turns antinuke protection OFF for this server.",
    "antinuke logs": "Sets the channel where antinuke alerts (with the False Ban button) are sent.",
    "staffrole": "Sets the Staff Team role — only this role (and admins) can ping roles or @everyone/@here.",
    "logs": "Sets the channel where full server activity logs (deletes, edits, joins, etc.) are sent.",
    "welcomechannel": "Sets the channel where welcome embeds are posted when someone joins.",
    "byechannel": "Sets the channel where goodbye embeds are posted when someone leaves.",
    "whitelist add": "Adds a user to the bot's whitelist (owner only).",
    "whitelist remove": "Removes a user from the bot's whitelist (owner only).",
    "whitelist list": "Shows everyone currently whitelisted.",
    "boostchannel": "Sets the channel where boost announcement embeds are posted.",
    "boostlogs": "Sets the channel where boost keys get logged.",
    "assetrole": "Sets the role given to members who redeem a boost key.",
    "serverboost test": "Sends a test boost embed + DM to you.",
    "redeem": "Redeems a boost key for asset-request access (key has multiple uses).",
    "check key": "Checks if a key is valid and how many uses it has left.",
    "application role set": "Sets the role auto-given to members who are 30+ days old and have 500+ messages.",
}


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


def get_keys():
    if not os.path.exists(BOOST_KEYS_FILE):
        return {}
    try:
        with open(BOOST_KEYS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


class Sin(commands.Cog):
    """Owns the entire `.sin` command tree (help, credits, antinuke settings, boost settings)."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="sin", invoke_without_command=True)
    async def sin(self, ctx, *, command_name: str = None):
        """`.sin` -> full command list. `.sin <command>` -> credit info for that command."""
        if command_name:
            key = command_name.lower().strip()
            if key in COMMAND_INFO:
                creator = self.bot.config.get("creator_name", "Unknown")
                embed = discord.Embed(
                    title=f"ℹ️ Command: {self.bot.config.get('prefix', '.')}{key}",
                    description=COMMAND_INFO[key],
                    color=discord.Color.blurple(),
                )
                embed.add_field(name="Credit", value=f"This command was created by **{creator}**.")
                await ctx.send(embed=embed)
            else:
                await ctx.send(
                    f"❌ No command called `{command_name}` found. Use `{self.bot.config.get('prefix','.')}sin` "
                    f"to see all commands."
                )
            return

        prefix = self.bot.config.get("prefix", ".")
        embed = discord.Embed(
            title="📜 All Commands",
            description=f"Prefix: `{prefix}`\nUse `{prefix}sin <command name>` to see who created a command and what it does.",
            color=discord.Color.gold(),
        )
        embed.add_field(
            name="🔨 Moderation",
            value=(
                f"`{prefix}ban @user [reason]`\n"
                f"`{prefix}unban <user_id>`\n"
                f"`{prefix}mute @user <duration> [reason]`\n"
                f"`{prefix}unmute @user`\n"
                f"`{prefix}role add @user @role`\n"
                f"`{prefix}role remove @user @role`\n"
                f"`{prefix}promote @user @role`\n"
                f"`{prefix}demote @user @role`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛡️ Antinuke",
            value=(
                f"`{prefix}sin antinuke` - check status\n"
                f"`{prefix}sin antinuke enable`\n"
                f"`{prefix}sin antinuke disable`\n"
                f"`{prefix}sin antinuke logs #channel` - alert channel (with False Ban button)\n"
                f"`{prefix}sin staffrole @role` - only this role + admins can ping roles/@everyone"
            ),
            inline=False,
        )
        embed.add_field(
            name="🤬 Antimod (Swear Filter)",
            value="Auto-deletes messages with blocked words and DMs the server owner. Edit `config.json` -> `swear_words` to customize.",
            inline=False,
        )
        embed.add_field(
            name="📝 Logging",
            value=f"`{prefix}sin logs #channel` - full activity log (deletes, edits, role/channel changes, joins/leaves, bans)",
            inline=False,
        )
        embed.add_field(
            name="👋 Welcome / Goodbye",
            value=(
                f"`{prefix}sin welcomechannel #channel`\n"
                f"`{prefix}sin byechannel #channel`"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔐 Whitelist",
            value=f"`{prefix}whitelist add/remove/list @user` - only whitelisted users can run any command",
            inline=False,
        )
        embed.add_field(
            name="🚀 Boosts",
            value=(
                f"`{prefix}sin boostchannel #channel` - where the boost embed is posted\n"
                f"`{prefix}sin boostlogs #channel` - where boost keys get logged\n"
                f"`{prefix}sin assetrole @role` - role given on redeem\n"
                f"`{prefix}sin check key <key>` - check if a key is valid + uses left\n"
                f"`{prefix}serverboost test` - test the boost flow\n"
                f"`{prefix}redeem <key>` - redeem your boost key (multi-use)"
            ),
            inline=False,
        )
        embed.add_field(
            name="📋 Applications / Auto-role",
            value=f"`{prefix}application role set @role` - auto-gives this role to members 30+ days old with 500+ messages",
            inline=False,
        )
        embed.set_footer(text=f"Credits via {prefix}sin <command>")
        await ctx.send(embed=embed)

    # ---------------- antinuke settings ----------------

    @sin.group(name="antinuke", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx):
        data = get_settings()
        g = get_guild(data, ctx.guild.id)
        enabled = g.get("antinuke_enabled", False)
        await ctx.send(
            f"🛡️ Antinuke is currently **{'ENABLED' if enabled else 'DISABLED'}**.\n"
            f"Use `{ctx.prefix}sin antinuke enable`, `{ctx.prefix}sin antinuke disable`, "
            f"or `{ctx.prefix}sin antinuke logs #channel`."
        )

    @antinuke.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def antinuke_enable(self, ctx):
        data = get_settings()
        g = get_guild(data, ctx.guild.id)
        g["antinuke_enabled"] = True
        save_settings(data)
        await ctx.send("✅ Antinuke protection has been **enabled**.")

    @antinuke.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def antinuke_disable(self, ctx):
        data = get_settings()
        g = get_guild(data, ctx.guild.id)
        g["antinuke_enabled"] = False
        save_settings(data)
        await ctx.send("✅ Antinuke protection has been **disabled**.")

    @antinuke.command(name="logs")
    @commands.has_permissions(administrator=True)
    async def antinuke_logs(self, ctx, channel: discord.TextChannel):
        data = get_settings()
        g = get_guild(data, ctx.guild.id)
        g["antinuke_log_channel"] = str(channel.id)
        save_settings(data)
        await ctx.send(f"✅ Antinuke log channel has been set to {channel.mention}.")


    # ---------------- check key snippet helper ----------------

    @sin.command(name="check")
    async def check_key(self, ctx, sub_action: str, key: str):
        if sub_action.lower() != "key":
            await ctx.send(f"Usage: `{ctx.prefix}sin check key <key_code>`")
            return
        
        keys = get_keys()
        key = key.strip().upper()
        entry = keys.get(key)
        
        if not entry:
            await ctx.send("❌ Key not found or has already expired.")
            return
            
        await ctx.send(
            f"ℹ️ **Key Details:** `{key}`\n"
            f"• Remaining Uses: **{entry.get('uses_left', 0)} / {entry.get('total_uses', 5)}**\n"
            f"• Associated Assets: **{entry.get('assets', 0)}**"
        )


async def setup(bot):
    await bot.add_cog(Sin(bot))
