import random
import string
import discord
import json
import os
from discord.ext import commands

# File paths to store data locally without needing a 'utils' library
SETTINGS_FILE = "guild_settings.json"
BOOST_COUNTS_FILE = "boost_counts.json"
BOOST_KEYS_FILE = "boost_keys.json"

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

def get_boost_counts():
    if not os.path.exists(BOOST_COUNTS_FILE):
        return {}
    try:
        with open(BOOST_COUNTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_boost_counts(data):
    try:
        with open(BOOST_COUNTS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def get_keys():
    if not os.path.exists(BOOST_KEYS_FILE):
        return {}
    try:
        with open(BOOST_KEYS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_keys(data):
    try:
        with open(BOOST_KEYS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def generate_key():
    return "-".join(
        "".join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)
    )

def perk_for_count(perks: dict, count: int):
    best = 0
    for tier_str, reward in perks.items():
        try:
            tier = int(tier_str)
        except ValueError:
            continue
        if count >= tier and reward > best:
            best = reward
    return best


class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_channel(self, guild, key):
        data = get_settings()
        g = get_guild(data, guild.id)
        cid = g.get(key)
        return guild.get_channel(int(cid)) if cid else None

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.premium_since is None and after.premium_since is not None:
            guild = after.guild
            counts = get_boost_counts()
            gid = str(guild.id)
            uid = str(after.id)
            counts.setdefault(gid, {})
            counts[gid][uid] = counts[gid].get(uid, 0) + 1
            save_boost_counts(counts)
            total_boosts = counts[gid][uid]

            perks = self.bot.config.get("boost_perks", {})
            reward = perk_for_count(perks, total_boosts)

            key = generate_key()
            keys = get_keys()
            total_uses = self.bot.config.get("key_uses", 5)
            keys[key] = {
                "guild_id": guild.id,
                "user_id": after.id,
                "boost_count": total_boosts,
                "assets": reward,
                "total_uses": total_uses,
                "uses_left": total_uses,
            }
            save_keys(keys)

            boost_channel = await self.get_channel(guild, "boost_channel")
            if boost_channel:
                embed = discord.Embed(
                    description=f"Hey {after.mention} we left you a little surprise! check the dm!!",
                    color=discord.Color.fuchsia(),
                )
                try:
                    await boost_channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    @commands.command(name="redeem")
    async def redeem(self, ctx, key: str):
        keys = get_keys()
        key = key.strip().upper()
        entry = keys.get(key)

        if not entry:
            await ctx.send("❌ That key doesn't exist or has expired.")
            return

        if entry["guild_id"] != ctx.guild.id:
            await ctx.send("❌ This key isn't valid in this server.")
            return
            
        await ctx.send("✅ Key successfully verified!")


async def setup(bot):
    await bot.add_cog(Boost(bot))
