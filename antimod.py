import discord
import json
import os
from discord.ext import commands

# File path to store data locally without needing a 'utils' library
SETTINGS_FILE = "guild_settings.json"

def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def get_guild(data, guild_id):
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {}
    return data[gid]


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_channel(self, guild, key):
        data = get_settings()
        g = get_guild(data, guild.id)
        cid = g.get(key)
        return guild.get_channel(int(cid)) if cid else None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = await self.get_channel(member.guild, "welcome_channel")
        if not channel:
            return
        embed = discord.Embed(
            title="👋 Welcome!",
            description=(
                f"{member.mention}, welcome to **{member.guild.name}**!\n"
                f"We're so glad to have you here, **{member.display_name}** — make yourself at home. 🎉"
            ),
            color=discord.Color.green(),
        )
        gif = self.bot.config.get("welcome_gif")
        if gif:
            embed.set_image(url=gif)
        embed.set_footer(text=f"Member #{member.guild.member_count}")
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await self.get_channel(member.guild, "goodbye_channel")
        if not channel:
            return
        embed = discord.Embed(
            title="👋 Goodbye",
            description=(
                f"**{member}** has left **{member.guild.name}**.\n"
                f"We're sad to see you go — take care, and the door's always open. 💔"
            ),
            color=discord.Color.dark_grey(),
        )
        gif = self.bot.config.get("goodbye_gif")
        if gif:
            embed.set_image(url=gif)
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass


async def setup(bot):
    await bot.add_cog(Welcome(bot))
