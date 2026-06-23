# Sin Bot — All-in-one Discord Bot

A Python (discord.py) bot with moderation, antinuke, an antimod swear filter, a
server-boost reward/key system, application auto-role, full server logging,
welcome/goodbye messages, and a global whitelist gate. Data is stored in simple
JSON files in `data/` (no database needed) — works fine on Railway with a small
attached volume (see below).

> **Bot identity:** prefix is `!`, display name target is `𝐬𝐢𝐧𝐢𝐬𝐦` (set in
> `config.json`). The bot will try to rename itself to match on startup, but
> Discord rate-limits username changes (~2/hour) — if it doesn't take, just
> rename it manually once in the Developer Portal → Bot tab, or wait an hour
> and restart.

## 🔐 Whitelist (access control)
Only users in `config.json` → `owner_ids`, or added via `!whitelist add @user`,
can run **any** bot command. Everyone else gets a "whitelist-only" message.
- `!whitelist add @user` (owner only)
- `!whitelist remove @user` (owner only)
- `!whitelist list`

## Commands

**Help / Credits**
- `.sin` — full command list
- `.sin <command name>` — shows who created that command + what it does

**Moderation**
- `.ban @user [reason]`
- `.unban <user_id>`
- `.mute @user <duration e.g. 10m/2h/1d> [reason]` (alias: `.timeout`)
- `.unmute @user`
- `.role add @user @role`
- `.role remove @user @role`
- `.promote @user @role`
- `.demote @user @role`

**Antinuke**
- `.sin antinuke` — show status
- `.sin antinuke enable`
- `.sin antinuke disable`
- `.sin antinuke logs #channel` — set the alert channel
- `.sin staffrole @role` — only this role (+ admins) can ping roles, @everyone, or @here

Detects mass channel deletions, mass role deletions, mass bans, mass kicks, and
repeated unauthorized role/@everyone pings (3+ actions by the same person within
10 seconds). When triggered:
1. The user is **instantly banned**
2. They get a DM: *"yo if you try that again you will be reported"*
3. The **server owner** and everyone with the **Staff Team role** get a DM with
   the full incident details (username, ID, tag, account creation date, action
   detected, action taken)
4. A full alert embed posts in the alert channel with a **"False Ban?" button**

**False Ban button** — only the server owner or whitelisted users can click it.
Clicking it:
- Unbans the user
- Sends them an apology DM with a fresh invite link
- Logs who reversed it

Outside of nuke detection, **any role ping or @everyone/@here from a non-staff,
non-admin member is deleted immediately** (no ban, just blocked) — only the
Staff Team role and admins can ping roles at all.

**Antimod (swear filter)** — no command, always on
- Deletes any message containing a word from `config.json` → `swear_words`
- DMs the **server owner** an embed with who said it, where, and what was deleted
- Edit the `swear_words` list in `config.json` to customize

**Server Boosts**
- `.sin boostchannel #channel` — where the "you got a surprise" embed posts
- `.sin boostlogs #channel` — where issued keys get logged for staff
- `.sin assetrole @role` — role given to someone who redeems a key
- `.sin check key <key>` — checks if a key is valid and how many uses are left
- `.serverboost test [boost_count]` — simulates the full flow on yourself (admin only)
- `.redeem <key>` — redeem a key for the asset-request role; each key has multiple
  uses (default 5, set via `config.json` → `key_uses`), so the same booster can
  redeem repeatedly until uses run out

When someone boosts the server:
1. An embed posts in the boost channel: *"Hey @user we left you a little surprise! check the dm!!"*
2. They get DM'd: thank-you message + their unique key + perk info
3. The key + boost count get logged in the boost-logs channel
4. They run `.redeem <key>` to get the configured role and request their free assets

Perk tiers (edit in `config.json` → `boost_perks`):
| Total boosts | Free assets |
|---|---|
| 1 | 5 |
| 2 | 12 |
| 3 | 15 |
| 5 | 100 |

> **Note:** Discord doesn't expose a "this user boosted N times" field directly —
> the bot tracks it itself, incrementing each time a member transitions from
> not-boosting to boosting. If someone unboosts and reboosts later, that counts
> as another boost. Use `.serverboost test <count>` to preview any tier.

**Applications / Auto-role**
- `.application role set @role` — every hour, the bot checks all members; anyone
  in the server 30+ days (configurable) with 500+ messages sent (configurable)
  automatically gets the role.

**Server Logging**
- `.sin logs #channel` — sends full activity logs: message delete/edit, role
  create/delete/update, channel create/delete, member join/leave, ban/unban.
  Each entry includes user info, action type, timestamp, and the
  channel/role involved.

**Welcome / Goodbye**
- `.sin welcomechannel #channel` — posts a welcome embed (with GIF) when someone joins
- `.sin byechannel #channel` — posts a goodbye embed (with GIF) when someone leaves
- GIFs are set in `config.json` → `welcome_gif` / `goodbye_gif`

## Setup

### 1. Create the bot application
1. Go to https://discord.com/developers/applications → New Application
2. Bot tab → Reset Token → copy it (this is your `DISCORD_TOKEN`)
3. Under **Privileged Gateway Intents**, enable:
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
4. OAuth2 → URL Generator → scopes: `bot`. Permissions: Administrator (simplest),
   or at minimum: Ban Members, Moderate Members (timeout), Manage Roles,
   Manage Channels (read audit log), View Audit Log, Send Messages, Embed Links.
5. Use the generated URL to invite the bot to your server.

### 2. Configure
Edit `config.json`:
- `prefix` — command prefix (default `!`)
- `bot_name` — desired display name (bot tries to self-rename on startup)
- `owner_ids` — **important:** put your real Discord user ID here (right-click
  your name in Discord with Developer Mode on → Copy User ID). Owners are
  always whitelisted and can manage the whitelist.
- `creator_name` — your name/credit shown in `.sin <command>`
- `swear_words` — list of words the antimod filter deletes
- `application_required_days` / `application_required_messages`
- `boost_perks` — boost-count → asset reward mapping
- `key_uses` — how many times a boost key can be redeemed
- `welcome_gif` / `goodbye_gif` — direct media URLs for the welcome/goodbye embeds
- `antinuke_warning_dm` — message sent to a banned nuke attempt

### 3. Run locally
```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your token
python bot.py
```

### 4. Deploy on Railway
1. Push this folder to a GitHub repo (or use Railway's CLI to deploy the folder directly).
2. In Railway: New Project → Deploy from GitHub repo (or `railway up` from this folder).
3. In the project's **Variables** tab, add `DISCORD_TOKEN` = your bot token.
4. Railway will use `railway.json` / `Procfile` automatically (`python bot.py`).
5. **Important:** the `data/` folder holds your JSON files. Railway's filesystem
   is ephemeral on redeploys unless you attach a **Volume**. In Railway:
   Project → your service → Settings → Volumes → add a volume mounted at
   `/app/data` so your warns, antinuke settings, boost keys, and message
   counts persist across deploys.

## File structure
```
bot.py                  # entrypoint
config.json             # editable settings
requirements.txt
Procfile / railway.json # Railway deploy config
.env.example
cogs/
  whitelist.py          # global whitelist gate
  sin.py                # .sin help/credits + all settings commands
  moderation.py         # ban/mute/timeout/role/promote/demote
  antinuke.py           # mass-action ban detection + role-ping permission gate
  antimod.py            # swear filter + message counting
  boost.py              # boost detection, multi-use keys, redeem, check key, test
  application.py        # 30-day/500-message auto-role
  logging_cog.py        # full server activity logging
  welcome.py             # welcome/goodbye embeds
utils/
  storage.py            # tiny JSON read/write helper
data/                   # auto-created JSON data files (gitignored)
```

## Important setup reminders
- After inviting the bot, run `.sin staffrole @YourStaffRole`, `.sin antinuke logs #channel`,
  `.sin logs #channel`, `.sin welcomechannel #channel`, and `.sin byechannel #channel` to
  wire everything up — nothing posts anywhere until those channels/roles are set.
- Add yourself to `owner_ids` in `config.json` **before** deploying, or you'll be locked
  out by the whitelist gate too.
- The bot needs `Ban Members`, `Manage Roles`, `Manage Messages`, `View Audit Log`,
  `Create Invite`, and `Moderate Members` permissions for the full feature set to work.
