import discord
from discord.ext import commands
import json
import os

WHITELIST_FILE = "whitelist.json"


def get_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "w") as f:
            json.dump({"users": []}, f)

    with open(WHITELIST_FILE, "r") as f:
        return json.load(f)


def save_whitelist(data):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_owner(bot, user_id):
    return user_id in bot.config.get("owner_ids", [])


def is_whitelisted(bot, user_id):
    if is_owner(bot, user_id):
        return True

    data = get_whitelist()
    return user_id in data.get("users", [])


class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_check(self.global_whitelist_check)

    async def global_whitelist_check(self, ctx):
        if is_whitelisted(self.bot, ctx.author.id):
            return True

        raise commands.CheckFailure(
            "🔒 This bot is whitelist-only. You don't have access to its commands."
        )

    @commands.group(name="whitelist", invoke_without_command=True)
    async def whitelist_group(self, ctx):
        await ctx.send(
            f"Use `{ctx.prefix}whitelist add @user`, "
            f"`{ctx.prefix}whitelist remove @user`, "
            f"or `{ctx.prefix}whitelist list`."
        )

    @whitelist_group.command(name="add")
    async def whitelist_add(self, ctx, member: discord.Member):
        if not is_owner(self.bot, ctx.author.id):
            return await ctx.send(
                "❌ Only bot owners can manage the whitelist."
            )

        data = get_whitelist()

        if member.id in data["users"]:
            return await ctx.send(
                f"⚠️ {member.mention} is already whitelisted."
            )

        data["users"].append(member.id)
        save_whitelist(data)

        await ctx.send(
            f"✅ {member.mention} has been added to the whitelist."
        )

    @whitelist_group.command(name="remove")
    async def whitelist_remove(self, ctx, member: discord.Member):
        if not is_owner(self.bot, ctx.author.id):
            return await ctx.send(
                "❌ Only bot owners can manage the whitelist."
            )

        data = get_whitelist()

        if member.id not in data["users"]:
            return await ctx.send(
                f"⚠️ {member.mention} isn't whitelisted."
            )

        data["users"].remove(member.id)
        save_whitelist(data)

        await ctx.send(
            f"✅ {member.mention} has been removed from the whitelist."
        )

    @whitelist_group.command(name="list")
    async def whitelist_list(self, ctx):
        data = get_whitelist()
        owners = self.bot.config.get("owner_ids", [])

        lines = [f"<@{uid}> (owner)" for uid in owners]
        lines += [
            f"<@{uid}>"
            for uid in data.get("users", [])
            if uid not in owners
        ]

        embed = discord.Embed(
            title="🔐 Whitelisted Users",
            description="\n".join(lines)
            if lines
            else "No one is whitelisted yet.",
            color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Whitelist(bot))
