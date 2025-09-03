import os
import sys
import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
from flask import Flask
from threading import Thread

# --- Fake audioop (nếu deploy ở Python >=3.12) ---
sys.modules['audioop'] = None

# --- Flask keep-alive (Render/Replit) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run).start()

# --- Load secrets ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AI_INSTRUCTION = os.getenv("AI_INSTRUCTION", "You are a helpful assistant.")

# --- Config Gemini ---
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Memory per user ---
chat_history = {}
chat_channels = {}  # guild_id -> channel_id

# --- Slash commands ---
@bot.tree.command(name="ask", description="Hỏi AI một câu hỏi")
async def ask(interaction: discord.Interaction, prompt: str):
    user_id = str(interaction.user.id)
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append({"role": "user", "content": prompt})

    response = model.generate_content(chat_history[user_id])
    reply = response.text
    chat_history[user_id].append({"role": "model", "content": reply})

    await interaction.response.send_message(reply)


@bot.tree.command(name="reset", description="Xóa lịch sử hội thoại với AI")
async def reset(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    chat_history[user_id] = []
    await interaction.response.send_message("✅ Đã reset hội thoại!")


@bot.tree.command(name="set_chat_channel", description="Đặt kênh chat AI cho server")
async def set_chat_channel(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    chat_channels[guild_id] = interaction.channel.id
    await interaction.response.send_message(f"✅ Đã đặt kênh này làm kênh chat AI!")


@bot.tree.command(name="unset_chat_channel", description="Xóa kênh chat AI của server")
async def unset_chat_channel(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id in chat_channels:
        del chat_channels[guild_id]
        await interaction.response.send_message("✅ Đã xóa kênh chat AI!")
    else:
        await interaction.response.send_message("❌ Server này chưa đặt kênh chat AI.")

# --- Events ---
@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync failed: {e}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = str(message.guild.id) if message.guild else None
    user_id = str(message.author.id)

    # Check mention hoặc kênh chat AI
    if bot.user in message.mentions or (guild_id in chat_channels and chat_channels[guild_id] == message.channel.id):
        if user_id not in chat_history:
            chat_history[user_id] = []

        chat_history[user_id].append({"role": "user", "content": message.content})
        response = model.generate_content(chat_history[user_id])
        reply = response.text
        chat_history[user_id].append({"role": "model", "content": reply})

        await message.channel.send(reply)

# --- Run ---
bot.run(DISCORD_TOKEN)
