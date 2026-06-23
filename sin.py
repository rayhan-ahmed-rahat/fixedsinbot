import time
import discord
import json
import os
from discord.ext import commands

THRESHOLD = 3        # number of nuke-style actions
WINDOW_SECONDS = 10   # within this many seconds triggers an instant ban

# File paths to store data locally without needing a 'utils' library
SETTINGS_FILE = "guild_settings.json"
UNBAN_LOG_FILE = "false_ban_log.json"

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

def get_unban_log():
    if not os.path.exists(UNBAN_LOG_FILE):
        return {"events": []}
    try:
        with open(UNBAN_LOG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"events": []}

def save_unban_log(data):
    try:
        with open(UNBAN_LOG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


class FalseBanView(discord.ui.View):
    """Persistent-ish view attached to the antinuke alert embed.
    Lets the owner / whitelisted staff reverse an automatic ban."""

    def __init__(self, bot, guild_id: int, user_id: int, user_tag: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.user_tag = user_tag

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        from whitelist import is_owner, is_whitelisted

        guild = interaction.guild
        is_guild_owner = guild is not None and interaction.user.id == guild.owner_id
        if is_guild_owner or is_owner(self.bot, interaction.user.id) or is_whitelisted(self.bot, interaction.user.id):
            return True
        await interaction.response.send_message(
            "❌ Only the server owner or whitelisted staff can use this button.", ephemeral=True
        )
        return False

    @discord.ui.button(label="False Ban?", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def false_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        try:
            user = await self.bot.fetch_user(self.user_id)
        except discord.NotFound:
            await interaction.response.send_message("❌ Couldn't find that user.", ephemeral=True)
            return

        try:
            await guild.unban(user, reason=f"False ban reversed by {interaction.user}")
        except discord.NotFound:
            await interaction.response.send_message("⚠️ That user isn't currently banned.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unban.", ephemeral=True)
            return

        invite_link = None
        try:
            for channel in guild.text_channels:
                perms = channel.permissions_for(guild.me)
                if perms.create_instant_invite:
                    invite = await channel.create_invite(max_age=86400, max_uses=1, reason="False ban apology invite")
                    invite_link = invite.url
                    break
        except discord.Forbidden:
            pass

        apology = discord.Embed(
            title="🙏 Apology — You Were Banned By Mistake",
            description=(
                f"We're really sorry — you were automatically banned from **{guild.name}** by our "
                f"anti-nuke system, but it turned out to be a false positive.\n\n"
                f"You're unbanned now. " + (f"Here's an invite back: {invite_link}" if invite_link else "Please ask a staff member for a new invite.")
            ),
            color=discord.Color.green(),
        )
        try:
            await user.send(embed=apology)
        except discord.Forbidden:
            pass

        log_data = get_unban_log()
        log_data["events"].append({
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "unbanned_by": interaction.user.id,
            "timestamp": discord.utils.utcnow().isoformat(),
        })
        save_unban_log(log_data)

        button.disabled = True
        button.label = "False Ban — Reversed"
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"✅ {self.user_tag} has been unbanned and sent an apology DM by {interaction.user.mention}.",
        )


class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # in-memory action tracker: {guild_id: {actor_id: [timestamps]}}
        self.actions = {}

    def is_enabled(self, guild_id):
        data = get_settings()
        g = get_guild(data, guild_id)
        return g.get("antinuke_enabled", False)

    def get_staff_role(self, guild):
        data = get_settings()
        g = get_guild(data, guild.id)
        role_id = g.get("staff_role")
        return guild.get_role(int(role_id)) if role_id else None

    async def get_log_channel(self, guild):
        data = get_settings()
        g = get_guild(data, guild.id)
        channel_id = g.get("antinuke_log_channel")
        if channel_id:
            return guild.get_channel(int(channel_id))
        return None

    async def log_event(self, guild, description, color=discord.Color.red()):
        channel = await self.get_log_channel(guild)
        if channel:
            embed = discord.Embed(title="🛡️ Antinuke Alert", description=description, color=color)
            embed.timestamp = discord.utils.utcnow()
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    async def record_and_check(self, guild, actor, action_label):
        """Returns True if this actor crossed the threshold and was punished."""
        if not self.is_enabled(guild.id):
            return False
        if actor is None or (actor.bot and actor.id == self.bot.user.id):
            return False
        now = time.time()
        g_acts = self.actions.setdefault(guild.id, {})
        timestamps = g_acts.setdefault(actor.id, [])
        timestamps.append(now)
        timestamps[:] = [t for t in timestamps if now - t <= WINDOW_SECONDS]
        if len(timestamps) >= THRESHOLD:
            timestamps.clear()
            await self.punish(guild, actor, action_label)
            return True
        return False

    async def punish(self, guild, actor, action_label):
        """Ban the offender, DM them a warning, alert owner + staff, and post a
        full alert embed (with a False Ban button) in the alert channel."""
        try:
            await guild.ban(actor, reason=f"Antinuke: mass {action_label} detected")
        except discord.Forbidden:
            pass
        except Exception:
            pass

        warning_text = self.bot.config.get("antinuke_warning_dm", "yo if you try that again you will be reported")
        try:
            await actor.send(embed=discord.Embed(description=warning_text, color=discord.Color.red()))
        except (discord.Forbidden, discord.HTTPException):
            pass

        account_created = discord.utils.format_dt(actor.created_at) if hasattr(actor, "created_at") else "Unknown"
        alert_embed = discord.Embed(
            title="🚨 Anti-Nuke Triggered",
            description="A user attempted to nuke the server and has been automatically banned. Full details below:",
            color=discord.Color.red(),
        )
        alert_embed.add_field(name="Username", value=str(actor), inline=True)
        alert_embed.add_field(name="User ID", value=str(actor.id), inline=True)
        alert_embed.add_field(name="Tag", value=f"<@{actor.id}>", inline=True)
        alert_embed.add_field(name="Account Created", value=account_created, inline=False)
        alert_embed.add_field(name="Action Detected", value=f"Mass {action_label} (nuke attempt)", inline=False)
        alert_embed.add_field(name="Action Taken", value="Banned automatically", inline=False)
        alert_embed.timestamp = discord.utils.utcnow()

        # DM the owner
        try:
            owner = guild.owner or await self.bot.fetch_user(guild.owner_id)
            await owner.send(embed=alert_embed)
        except Exception:
            pass

        # DM the staff role members
        staff_role = self.get_staff_role(guild)
        if staff_role:
            for member in staff_role.members:
                try:
                    await member.send(embed=alert_embed)
                except Exception:
                    pass

async def setup(bot):
    await bot.add_cog(Antinuke(bot))
