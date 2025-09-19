import sys
import discord
from discord.ext import commands
import google.generativeai as genai
import os
from flask import Flask
from threading import Thread

sys.modules['audioop'] = None
from dotenv import load_dotenv

# --- Phần 1: Token hoặc key ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
AI_INSTRUCTION = os.getenv('AI_INSTRUCTION')

if not DISCORD_TOKEN or not GOOGLE_API_KEY:
    print("LỖI: Vui lòng thiết lập DISCORD_TOKEN và GOOGLE_API_KEY trong tệp .env")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

# --- Phần 2: Thiết lập mô hình AI ---
model = genai.GenerativeModel('gemini-2.5-flash')

# --- Phần 3: Bộ nhớ hội thoại cho từng user ---
user_chats = {}
OWNER_ID = 1067374135220649985  

# Hàm hoiai không phải async, nên bỏ await khi gọi
def hoiai(user_id: int, username: str, question: str) -> str:
    global user_chats
    try:
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])

        if user_id == OWNER_ID:
            display_name = "Anh Đạt"
        else:
            display_name = username

        hidden_instruction = AI_INSTRUCTION if AI_INSTRUCTION else ""
        prompt = f"{hidden_instruction}\n\n{display_name} hỏi: {question}"

        response = user_chats[user_id].send_message(prompt)
        return response.text
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API: {e}")
        return "Xin lỗi, em bị sự cố khi kết nối với bộ não AI 🧠💥"

async def send_long_message(channel, text: str):
    if len(text) <= 2000:
        await channel.send(text)
    elif len(text) <= 6000:
        embed = discord.Embed(description=text[:4096], color=0x00ff00)
        if len(text) > 4096:
            embed.add_field(name="Phần tiếp theo", value=text[4096:4096+1024], inline=False)
        await channel.send(embed=embed)
    else:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for i, chunk in enumerate(chunks, 1):
            embed = discord.Embed(description=chunk, color=0x00ff00)
            embed.set_footer(text=f"Trang {i}/{len(chunks)}")
            await channel.send(embed=embed)

# --- Phần 4: Thiết lập Bot Discord ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
chat_channel_id = None

@bot.event
async def on_ready():
    print(f'Bot {bot.user} đã online rồi 😎')
    print(f'{AI_INSTRUCTION}')
    print('________________________________')
    try:
        synced = await bot.tree.sync()
        print(f"Đã đồng bộ {len(synced)} lệnh.")
    except Exception as e:
        print(f"Lỗi khi đồng bộ lệnh: {e}")

#lệnh/
@bot.tree.command(name="text", description="The bot will print out the text you want to send")
async def text(interaction: discord.Interaction, printer: str):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(printer)
@bot.tree.command(name="clear", description="Xóa tin nhắn")
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.send_message("Đang dọn dẹp tin nhắn...", ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.channel.send(f"✅ Đã dọn dẹp {amount} tin nhắn.")
@bot.tree.command(name="set_channel", description="Thiết lập kênh này là kênh bot tự động trả lời.")
@commands.has_permissions(manage_channels=True)
async def set_channel(interaction: discord.Interaction):
    global chat_channel_id
    chat_channel_id = interaction.channel_id
    await interaction.response.send_message(f"✅ Dạ Mikasa sẽ trả lời ở kênh này ạ.(<#{chat_channel_id}>)ở chỗ khác thì có thể @ để em trả lời")
    print(f"Kênh chat AI được thiết lập: {interaction.channel.name} (ID: {chat_channel_id})")

@bot.tree.command(name="unset_channel", description="Hủy bỏ kênh bot tự động trả lời.")
@commands.has_permissions(manage_channels=True)
async def unset_channel(interaction: discord.Interaction):
    global chat_channel_id
    if chat_channel_id is not None:
        chat_channel_id = None
        await interaction.response.send_message("❌ Kênh chat AI tự động đã được hủy bỏ.")
        print("Kênh chat AI tự động đã được hủy bỏ.")
    else:
        await interaction.response.send_message("Không có kênh nào được thiết lập làm kênh chat AI.")

@bot.tree.command(name="ask", description="Hỏi AI một câu nhanh")
async def ask(interaction: discord.Interaction, *, question: str, ephemeral: bool):
    await interaction.response.defer(ephemeral=ephemeral) 
    answer = hoiai(interaction.user.id, interaction.user.display_name, question)
    await interaction.followup.send(answer, ephemeral=ephemeral)
@bot.tree.command(name="reset", description="Xóa bộ nhớ hội thoại AI (riêng cho bạn)")
async def reset(interaction: discord.Interaction):
    global user_chats
    user_chats[interaction.user.id] = model.start_chat(history=[])
    await interaction.response.send_message("🧹 Bộ nhớ hội thoại AI của bạn đã được reset!")

@bot.event
async def on_message(message):
    global chat_channel_id
    if message.author == bot.user:
        return
    if message.content.startswith(';Mika'):
        await message.channel.send(f'dạ {message.author.mention},em đây😚')
    if message.content.lower().startswith('mika!'):
        await message.channel.send(f'dạ {message.author.mention},em đây😚')
        return
    is_in_chat_channel = (message.channel.id == chat_channel_id)
    is_bot_mentioned = bot.user.mentioned_in(message)
    if is_in_chat_channel or is_bot_mentioned:
        question = (
            message.content
            .replace(f'<@!{bot.user.id}>', '')
            .replace(f'<@{bot.user.id}>', '')
            .strip()
        )
        if question:
            async with message.channel.typing():
                print(f"Nhận câu hỏi từ '{message.author}' ở kênh {'tự động' if is_in_chat_channel else 'thường'}: {question}")
                answer = hoiai(message.author.id, message.author.display_name, question)
                print(f"Gửi câu trả lời: {answer}")
                # Dùng send_long_message ở đây là đúng
                await send_long_message(message.channel, answer)
    await bot.process_commands(message)

# --- Phần 5: Thiết lập Flask Web Server ---
app = Flask('')

@app.route('/')
def home():
    return "bé còn on nha 😘🥰!"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Phần 6: Chạy Bot ---
print("Đang khởi động web server...")
keep_alive()
print("Đang khởi động bot...")
bot.run(DISCORD_TOKEN)
