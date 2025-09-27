import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 1. Tải biến môi trường
load_dotenv()
# Đảm bảo tên biến môi trường là "DISCORD_TOKEN" hoặc "TOKENBOT"
# Tôi giữ nguyên tên biến của anh, nhưng nên kiểm tra file .env
TOKEN = os.getenv("TOKENBOT")

# ID của Owner
OWNER_ID = 1067374135220649985

# 2. Định nghĩa hàm load/save admins
def load_admins():
    """Tải danh sách admin từ file admins.json. Nếu file không tồn tại, tạo file mới."""
    try:
        if not os.path.exists("admins.json"):
            # Nếu file không tồn tại, tạo file với OWNER_ID là admin duy nhất
            with open("admins.json", "w") as f:
                json.dump({"admins": [OWNER_ID]}, f, indent=4)
        
        with open("admins.json", "r") as f:
            data = json.load(f)
            # Đảm bảo OWNER_ID luôn có trong danh sách admin
            if OWNER_ID not in data.get("admins", []):
                data["admins"].append(OWNER_ID)
                save_admins(data["admins"]) # Lưu lại nếu có thay đổi
            return data.get("admins", [])
    except Exception as e:
        print(f"Lỗi khi tải admin: {e}")
        return [OWNER_ID] # Trả về OWNER_ID nếu có lỗi

def save_admins(admins_list):
    try:
        unique_admins = list(set(admins_list + [OWNER_ID]))
        with open("admins.json", "w") as f:
            json.dump({"admins": unique_admins}, f, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu admin: {e}")

# Tải danh sách admin khi bot khởi động
admins = load_admins()

# 3. Cấu hình Intents và Bot
intents = discord.Intents.default()
# Cần các intents này cho các lệnh như clear, ban, mute, và theo dõi thành viên
intents.message_content = True
intents.members = True
intents.guilds = True # Đảm bảo bot có thể thấy thông tin guild

bot = commands.Bot(command_prefix='!', intents=intents)

# Hàm kiểm tra quyền đã được tối ưu một chút
def has_power(interaction: discord.Interaction, permission: str) -> bool:
    """Kiểm tra quyền của người dùng (Owner > Admin > Guild Permissions)."""
    if interaction.user.id == OWNER_ID:
        return True
    
    if interaction.user.id in admins:
        return True
    
    # Kiểm tra quyền trong Guild/Server
    if interaction.user.guild_permissions:
        return getattr(interaction.user.guild_permissions, permission, False)
        
    return False

# --- Events ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} đã online rồi 😎')
    try:
        # Đồng bộ hóa lệnh Slash Command
        synced = await bot.tree.sync()
        print(f"hiện tại bot có {len(synced)} lệnh.")
    except Exception as e:
        print(f"Lỗi sync: {e}")

# --- Commands ---

@bot.tree.command(name="clear", description="Xóa tin nhắn trong kênh, có thể chọn user")
async def clear(interaction: discord.Interaction, amount: int, user: discord.User = None):
    # Dùng `manage_messages` là đúng
    if not has_power(interaction, "manage_messages"):
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True)
        return

    # Lệnh purge của Discord chỉ cho phép xóa tin nhắn < 14 ngày.
    # Anh đang dùng `after=datetime.now() - timedelta(days=14)`, điều này sẽ chỉ xóa 
    # các tin nhắn **MỚI HƠN** 14 ngày.
    # Để đơn giản, chỉ cần bỏ tham số `after` đi, Discord sẽ tự động xử lý.
    # Nếu muốn xóa tất cả tin nhắn gần nhất:
    # Tuy nhiên, lệnh purge có giới hạn tối đa, ta nên tách ra khỏi logic chính.
    
    # Gửi phản hồi tạm thời
    await interaction.response.send_message("🧹 Đang dọn tin nhắn...", ephemeral=True)

    # Hàm check_user để lọc tin nhắn
    def check_user(msg):
        # Kiểm tra tin nhắn của user cụ thể (nếu user được chỉ định)
        if user:
            return msg.author == user
        # Nếu không chỉ định user, chấp nhận tất cả
        return True

    try:
        # Lệnh purge thực hiện việc xóa tin nhắn
        deleted = await interaction.channel.purge(limit=amount, check=check_user)
        
        # Gửi thông báo kết quả qua `followup`
        if user:
            # Dùng `display_name` thay vì `mention` trong ephemeral message sẽ đẹp hơn
            await interaction.followup.send(f"✅ Đã xóa **{len(deleted)}** tin nhắn của **{user.display_name}**.", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ Đã xóa **{len(deleted)}** tin nhắn gần nhất.", ephemeral=True)
            
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot không có quyền `Quản lý tin nhắn` để thực hiện lệnh này.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ Lỗi khi xóa tin nhắn: {e}", ephemeral=True)

@bot.tree.command(name="ban", description="Ban 1 user khỏi server")
async def ban(interaction: discord.Interaction, user: discord.User, reason: str = "Không có lý do"):
    if not has_power(interaction, "ban_members"):
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True)
        return
        
    # Cải tiến: Lấy Member object bằng `fetch_member` nếu không có sẵn
    member = interaction.guild.get_member(user.id)
    if not member:
        # Nếu không phải member trong server (ví dụ: đã rời đi) thì vẫn có thể ban bằng User ID.
        pass
    else:
        # Các kiểm tra quyền lực vẫn giữ nguyên:
        if member == interaction.guild.me:
            await interaction.response.send_message("❌ Không thể ban chính Bot.", ephemeral=True)
            return
        
        # Vai trò của người dùng không được bằng hoặc cao hơn người ra lệnh (trừ Owner)
        if interaction.user.top_role <= member.top_role and interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Bạn không thể ban người có vai trò bằng hoặc cao hơn bạn.", ephemeral=True)
            return

    try:
        await interaction.guild.ban(user, reason=reason)
        await interaction.response.send_message(f"🚫 **{user.mention}** đã bị ban. Lý do: **{reason}**")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot không có quyền `Cấm thành viên` hoặc vai trò của Bot thấp hơn.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Lỗi: {e}", ephemeral=True)

# Các lệnh `unban`, `mute`, `unmute`, `thêm admin`, `xoa admin`, `listadmin`, `text`
# Về cơ bản đã hoạt động đúng logic. Tôi giữ nguyên.
@bot.tree.command(name="unban", description="Gỡ ban một user bằng ID")
async def unban(interaction: discord.Interaction, user_id: str):
    if not has_power(interaction, "ban_members"):
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True)
        return
    try:
        user_id_int = int(user_id)
        # Sử dụng `bot.fetch_user` để lấy User object từ ID
        user = await bot.fetch_user(user_id_int) 
        
        # Nếu người dùng không bị ban, lệnh này sẽ raise discord.NotFound
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ **{user.mention}** đã được gỡ ban")
    except ValueError:
        await interaction.response.send_message("❌ ID người dùng không hợp lệ.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("⚠️ Người dùng này không bị ban hoặc ID không tồn tại.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot không có quyền `Cấm thành viên` để gỡ ban.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="mute", description="Cấm chat 1 user trong một khoảng thời gian (phút)")
async def mute(interaction: discord.Interaction, user: discord.User, minutes: int):
    if not has_power(interaction, "moderate_members"):
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True)
        return
        
    member = interaction.guild.get_member(user.id)
    if not member:
        await interaction.response.send_message("⚠️ Không tìm thấy người dùng này trong server.", ephemeral=True)
        return
    
    if minutes <= 0:
        await interaction.response.send_message("❌ Số phút phải lớn hơn 0.", ephemeral=True)
        return
    
    if interaction.user.top_role <= member.top_role and interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bạn không thể mute người có vai trò bằng hoặc cao hơn bạn.", ephemeral=True)
        return

    try:
        # Discord có giới hạn timeout tối đa là 28 ngày (40320 phút)
        if minutes > 40320:
             await interaction.response.send_message("❌ Thời gian mute tối đa là 28 ngày (40320 phút).", ephemeral=True)
             return
             
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=f"Mute {minutes} phút bởi {interaction.user.name}")
        
        await interaction.response.send_message(f"🔇 **{user.mention}** đã bị mute **{minutes} phút!**")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot không có quyền `Kiểm duyệt thành viên` (Moderate Members) hoặc vai trò của Bot thấp hơn.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="unmute", description="Gỡ mute một user")
async def unmute(interaction: discord.Interaction, user: discord.User):
    if not has_power(interaction, "moderate_members"):
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True)
        return
        
    member = interaction.guild.get_member(user.id)
    if not member:
        await interaction.response.send_message("⚠️ Không tìm thấy người dùng này trong server.", ephemeral=True)
        return
    
    if interaction.user.top_role <= member.top_role and interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bạn không thể gỡ mute người có vai trò bằng hoặc cao hơn bạn.", ephemeral=True)
        return
        
    try:
        # Gỡ timeout bằng cách đặt thời gian timeout là None
        await member.timeout(None, reason=f"Unmute bởi {interaction.user.name}")
        
        await interaction.response.send_message(f"🔊 **{user.mention}** đã được gỡ mute!")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot không có quyền `Kiểm duyệt thành viên` (Moderate Members) hoặc vai trò của Bot thấp hơn.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="themadmin", description="Thêm 1 admin mới (chỉ Owner dùng được)")
async def add_admin(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này!", ephemeral=True)
        return
    
    # Không thể thêm chính Bot làm admin
    if user.id == bot.user.id:
        await interaction.response.send_message("❌ Không thể thêm Bot làm admin.", ephemeral=True)
        return
        
    if user.id in admins:
        await interaction.response.send_message("⚠️ Người này đã là admin rồi!", ephemeral=True)
    else:
        admins.append(user.id)
        save_admins(admins)
        await interaction.response.send_message(f"✅ Đã thêm **{user.mention}** làm admin!", ephemeral=False)

@bot.tree.command(name="xoaadmin", description="Xóa 1 admin (chỉ Owner dùng được)")
async def remove_admin(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này!", ephemeral=True)
        return
    if user.id not in admins:
        await interaction.response.send_message("⚠️ Người này không phải admin!", ephemeral=True)
    elif user.id == OWNER_ID:
        await interaction.response.send_message("❌ Không thể xóa Owner (chính bạn) khỏi danh sách admin!", ephemeral=True)
    else:
        admins.remove(user.id)
        save_admins(admins)
        await interaction.response.send_message(f"🗑️ Đã xóa **{user.mention}** khỏi admin!", ephemeral=False)

@bot.tree.command(name="listadmin", description="Xem danh sách admin hiện tại")
async def list_admin(interaction: discord.Interaction):
    
    # Tải lại danh sách admin để đảm bảo luôn mới nhất
    current_admins = load_admins()
    
    if not current_admins:
        # Điều này hiếm xảy ra vì OWNER_ID luôn có
        await interaction.response.send_message("⚠️ Hiện tại chưa có admin nào ngoài Owner!", ephemeral=True)
        return
    
    mentions = []
    for uid in current_admins:
        # Lấy User object
        user = bot.get_user(uid)
        if user:
            # Nếu là Owner thì thêm ký hiệu đặc biệt
            if uid == OWNER_ID:
                mentions.append(f"👑 **Owner:** {user.mention} ({user.display_name})")
            else:
                mentions.append(f"👨‍💻 **Admin:** {user.mention} ({user.display_name})")
        else:
            mentions.append(f"❌ **ID không tìm thấy:** <@{uid}>")
            
    text = "📜 **Danh sách admin hiện tại:**\n" + "\n".join(mentions)
    await interaction.response.send_message(text, ephemeral=False)

@bot.tree.command(name="text", description="Nhập để Xuân Quỳnh gửi vào chat")
async def text(interaction: discord.Interaction, inra: str):
    # Kiểm tra quyền: Owner hoặc Admin
    if interaction.user.id not in admins:
        await interaction.response.send_message("❌ Bạn không có quyền để gửi tin nhắn này!", ephemeral=True)
    else:
        # Gửi phản hồi ephemeral trước
        await interaction.response.send_message(f"✅ Tin nhắn đã được gửi: **[{inra}]**", ephemeral=True)
        # Sau đó gửi tin nhắn vào kênh chat
        await interaction.channel.send(inra)

# 5. Chạy Bot (Sửa lỗi khởi động chính)
if TOKEN is None:
    print("❌ LỖI: Không tìm thấy biến môi trường 'TOKENBOT'.")
else:
    try:
        # Sử dụng biến TOKEN đã load từ os.getenv
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ LỖI ĐĂNG NHẬP: Token không hợp lệ. Vui lòng kiểm tra lại TOKENBOT trong file .env")
    except Exception as e:
        print(f"⚠️ LỖI KHỞI ĐỘNG BOT: {e}")

