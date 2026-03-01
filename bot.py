import discord
from discord.ext import commands
import datetime
import asyncio
import os

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- CONFIG ----------
PROOF_CHANNEL_ID = 1467104586329362677
LOG_CHANNEL_ID = 1458565222926123109
ROLE_ID = 1458568198214516991
REQUIRED = 7
ROLE_DURATION_HOURS = 24

# UserID -> Screenshot Counter
user_counter = {}

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")

# ---------- ROLE TIMER ----------
async def remove_role_later(guild, user_id):
    await asyncio.sleep(ROLE_DURATION_HOURS * 3600)

    member = guild.get_member(user_id)
    role = guild.get_role(ROLE_ID)

    if member and role and role in member.roles:
        await member.remove_roles(role)
        print(f"⏱️ Rolle entfernt von {member}")

# ---------- MESSAGE EVENT ----------
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # Nur im Proof Channel arbeiten
    if message.channel.id == PROOF_CHANNEL_ID:

        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        # ❌ Wenn keine Anhänge -> löschen + loggen
        if not message.attachments:
            await message.delete()

            if log_channel:
                await log_channel.send(
                    f"🗑️ Deleted text message from {message.author.mention}"
                )
            return

        # Nur Bilder erlauben
        images = [
            a for a in message.attachments
            if a.content_type and a.content_type.startswith("image/")
        ]

        # ❌ Wenn Anhänge aber keine Bilder -> löschen
        if not images:
            await message.delete()

            if log_channel:
                await log_channel.send(
                    f"🗑️ Deleted non-image file from {message.author.mention}"
                )
            return

        # -----------------------------
        # Ab hier sind nur Bilder erlaubt
        # -----------------------------

        user_id = message.author.id
        user_counter[user_id] = user_counter.get(user_id, 0) + len(images)
        count = user_counter[user_id]

        # ❌ Noch nicht genug Screenshots
        if count < REQUIRED:
            if log_channel:
                await log_channel.send(
                    f"❌ {message.author.mention} – {count}/{REQUIRED} screenshots received."
                )
            return

        # ✅ Approved
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if log_channel:
            await log_channel.send(
                f"✅ {message.author.mention} approved at {now}. Role valid for 24h 😈"
            )

        member = message.guild.get_member(user_id)
        role = message.guild.get_role(ROLE_ID)

        if member and role:
            await member.add_roles(role)
            print(f"✅ Rolle vergeben an {member}")

            # 24h Timer starten
            bot.loop.create_task(remove_role_later(message.guild, user_id))

        # Counter zurücksetzen
        user_counter.pop(user_id, None)

    await bot.process_commands(message)

# ---------- START ----------
bot.run(os.environ["DISCORD_TOKEN"])
