# --- Phần 1: Nhập các thư viện cần thiết ---
import discord
from discord.ext import commands
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- Phần 2: Tải và cấu hình các khóa bí mật ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not DISCORD_TOKEN or not GOOGLE_API_KEY:
    print("LỖI: Vui lòng thiết lập DISCORD_TOKEN và GOOGLE_API_KEY trong tệp .env")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

# --- Phần 3: Thiết lập mô hình AI ---
model = genai.GenerativeModel('gemini-2.5-pro')

def hoiai(question):
    """
    Hàm này gửi câu hỏi đến Google AI và trả về câu trả lời.
    """
    try:
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API: {e}")
        return "Xin lỗi, tôi gặp sự cố khi kết nối với bộ não AI của mình. 🧠💥"

# --- Phần 4: Thiết lập Bot Discord ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- Phần 5: Định nghĩa các sự kiện cho Bot ---

@bot.event
async def on_ready():
    """
    Sự kiện này sẽ chạy một lần khi bot kết nối thành công với Discord.
    """
    print(f'Bot đã đăng nhập với tên {bot.user}')
    print('Bot đã sẵn sàng nhận câu hỏi!')
    print('----------------------------------')

@bot.event
async def on_message(message):
    """
    Sự kiện này chạy mỗi khi có một tin nhắn mới trong bất kỳ kênh nào mà bot có thể thấy.
    """
    # 1. Bỏ qua tin nhắn từ chính bot
    if message.author == bot.user:
        return

    # 2. Kiểm tra xem bot có được @tag (nhắc đến) trong tin nhắn không
    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            # Lấy nội dung câu hỏi (đã loại bỏ phần @tag)
            question = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()

            # *** THAY ĐỔI Ở ĐÂY ***
            # Bây giờ chúng ta không kiểm tra câu hỏi đặc biệt nữa,
            # mà gửi thẳng câu hỏi đến hàm `hoiai` để AI xử lý.
            print(f"Nhận câu hỏi từ '{message.author}': {question}")
            answer = hoiai(question)
            print(f"Gửi câu trả lời: {answer[:50]}...")

            # Gửi câu trả lời lại kênh
            await message.reply(answer)

# --- Phần 6: Chạy Bot ---
print("Đang khởi động bot...")
bot.run(DISCORD_TOKEN)
      
