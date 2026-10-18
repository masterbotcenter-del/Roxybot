# telebot_converter.py
import telebot
from telebot import types
from pymongo import MongoClient
from bson.objectid import ObjectId
import re
import psutil
import time
import logging
import requests  # ← YEH ADD KARO
from datetime import datetime, timedelta  # ← YEH BHI ADD KARO
from typing import Dict, List, Union

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration (kept from your original)
API_ID = 27060347
API_HASH = "cfeaa1637b54e9e321b458790b915ee4"
BOT_TOKEN = "8556509637:AAG_bxAKxGiBNeZPytsbBV4w20X9abCSPpA"
ADMIN_ID = 8302055186
OTHER_ADMINS = [8342566909, 0000000000]
MONGO_URL = "mongodb+srv://masterbotcenter_db_user:@roxybotuser.ucjt1bs.mongodb.net"

# NEW: Logs Channel
LOGS_CHANNEL = -1003206187926  # Apna private channel ID yahan dalo
# Global variable for bot start time
BOT_START_TIME = time.time()
# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="html")

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["anime_filter_bot"]
filters_collection = db["filters"]
users_collection = db["users"]
groups_collection = db["groups"]

# DM Only Filters Collections
dm_filters_collection = db["dm_filters"]
dm_settings_collection = db["dm_settings"]

# NEW: Logs Function
def log_message(log_type: str, message: str, user_id: int = None, chat_id: int = None, 
                username: str = None, first_name: str = None, chat_title: str = None, 
                extra_data: str = ""):
    """Send detailed log message to logs channel"""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        log_text = f"""🪵 <b>LOG TYPE:</b> {log_type}
⏰ <b>TIME:</b> <code>{timestamp}</code>"""

        if user_id:
            log_text += f"\n👤 <b>USER ID:</b> <code>{user_id}</code>"
        
        if first_name:
            log_text += f"\n👨‍💼 <b>NAME:</b> {first_name}"
        
        if username:
            log_text += f"\n📎 <b>USERNAME:</b> @{username}" if username else "\n📎 <b>USERNAME:</b> No username"
        
        if chat_id:
            if chat_id == user_id:
                log_text += f"\n💬 <b>CHAT:</b> Private Chat"
            else:
                log_text += f"\n💬 <b>CHAT ID:</b> <code>{chat_id}</code>"
        
        if chat_title:
            log_text += f"\n🏷️ <b>GROUP:</b> {chat_title}"
        
        if message:
            log_text += f"\n📝 <b>MESSAGE:</b> {message}"
        
        if extra_data:
            log_text += f"\n📊 <b>EXTRA:</b> {extra_data}"

        bot.send_message(LOGS_CHANNEL, log_text, parse_mode="HTML")
        
    except Exception as e:
        logger.exception("log_message failed: %s", e)
        
        #new log mtlb jo bhi user bot me likhega send krega bot batayega

        
        #ider vo complete hota hai new logs wala
        
        
        
#pingggggggg
def get_bot_uptime():
    """Calculate actual bot uptime"""
    try:
        current_time = time.time()
        uptime_seconds = current_time - BOT_START_TIME
        
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        return f"{hours:02d}ʜ:{minutes:02d}ᴍ:{seconds:02d}s"
    except Exception:
        return "00ʜ:00ᴍ:00s"        
        

# DM Filters Settings Management
def get_dm_settings():
    settings = dm_settings_collection.find_one({"_id": "global_settings"})
    if not settings:
        settings = {
            "_id": "global_settings",
            "dm_filters_enabled": False,
            "creation_mode": False, 
            "global_groups_enabled": False,
            "enabled_groups": [],
            "disabled_groups": []  # NEW: Track disabled groups separately
        }
        dm_settings_collection.insert_one(settings)
    return settings

def update_dm_settings(update_data):
    dm_settings_collection.update_one(
        {"_id": "global_settings"},
        {"$set": update_data},
        upsert=True
    )

# DM Only Filters Functions
def save_dm_filter(keyword: str, filter_data: Dict):
    upsert_doc = {"keyword": keyword, **filter_data}
    dm_filters_collection.update_one(
        {"keyword": {"$regex": f"^{re.escape(keyword)}$", "$options": "i"}},
        {"$set": upsert_doc},
        upsert=True
    )

def delete_dm_filter(keyword: str):
    result = dm_filters_collection.delete_one({"keyword": {"$regex": f"^{re.escape(keyword)}$", "$options": "i"}})
    return result.deleted_count > 0

def get_dm_filter(keyword: str) -> Union[Dict, None]:
    return dm_filters_collection.find_one({"keyword": {"$regex": f"^{re.escape(keyword)}$", "$options": "i"}})

def get_dm_filter_by_id(id_str: str) -> Union[Dict, None]:
    try:
        return dm_filters_collection.find_one({"_id": ObjectId(id_str)})
    except Exception:
        return None

def get_all_dm_filters() -> List[Dict]:
    return list(dm_filters_collection.find({}).sort("keyword", 1))

def is_dm_filter_enabled_for_group(chat_id: int) -> bool:
    """Check if DM filters are enabled for specific group"""
    settings = get_dm_settings()
    
    # If global groups are disabled, check individual group settings
    if not settings["global_groups_enabled"]:
        return chat_id in settings["enabled_groups"]
    
    # If global groups are enabled, check if group is not specifically disabled
    return chat_id not in settings["disabled_groups"]

# Original Helper DB functions (unchanged)
def save_filter(keyword: str, filter_data: Dict):
    upsert_doc = {"keyword": keyword, **filter_data}
    filters_collection.update_one(
        {"keyword": {"$regex": f"^{re.escape(keyword)}$", "$options": "i"}},
        {"$set": upsert_doc},
        upsert=True
    )

def delete_filter(keyword: str):
    result = filters_collection.delete_one({"keyword": {"$regex": f"^{re.escape(keyword)}$", "$options": "i"}})
    return result.deleted_count > 0

def get_filter(keyword: str) -> Union[Dict, None]:
    return filters_collection.find_one({"keyword": {"$regex": f"^{re.escape(keyword)}$", "$options": "i"}})

def get_filter_by_id(id_str: str) -> Union[Dict, None]:
    try:
        return filters_collection.find_one({"_id": ObjectId(id_str)})
    except Exception:
        return None

def get_all_filters() -> List[Dict]:
    return list(filters_collection.find({}).sort("keyword", 1))

def update_user_data(user_id: int, chat_id: int):
    """
    BUG FIX: Only count as user if they're in PRIVATE chat (actually started bot)
    Always count groups separately
    """
    # Only add to users collection if it's PRIVATE chat (user actually started bot)
    if chat_id == user_id:  # This means private chat
        users_collection.update_one(
            {"user_id": user_id, "bot_token": bot.token},
            {"$set": {"user_id": user_id, "bot_token": bot.token}},
            upsert=True
        )
    
    # Always update groups if it's a group chat
    if chat_id != user_id:
        groups_collection.update_one(
            {"chat_id": chat_id, "bot_token": bot.token},
            {"$set": {"chat_id": chat_id, "bot_token": bot.token}},
            upsert=True
        )

def get_user_count() -> int:
    return users_collection.count_documents({"bot_token": bot.token})

def get_group_count() -> int:
    return groups_collection.count_documents({"bot_token": bot.token})

def short_display(text: str, limit: int = 50) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit-3] + "..."

ANIME_KEYBOARD_LETTERS = [
    ["0","1","2","3","4","5","6","7","8","9"],
    ["A","B","C","D","E","F","G","H","I","J","K","L","M"],
    ["N","O","P","Q","R","S","T","U","V","W","X","Y","Z"],
    ["Other"]
]

def make_inline_keyboard(button_rows):
    ik = types.InlineKeyboardMarkup()
    for row in button_rows:
        ik.row(*row)
    return ik

def make_reply_keyboard(rows):
    rk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for row in rows:
        rk.row(*[types.KeyboardButton(text) for text in row])
    return rk

def send_copy_to_chat(target_chat_id: int, src_msg):
    try:
        if src_msg.content_type == "text":
            bot.send_message(target_chat_id, src_msg.text)
        elif src_msg.content_type == "photo":
            file_id = src_msg.photo[-1].file_id
            caption = src_msg.caption or ""
            bot.send_photo(target_chat_id, file_id, caption=caption)
        else:
            bot.forward_message(target_chat_id, src_msg.chat.id, src_msg.message_id)
        return True
    except Exception as e:
        logger.exception("send_copy_to_chat failed: %s", e)
        return False

# NEW: DM Only Filters Commands

@bot.message_handler(commands=["openfilter"])
def open_dm_filter(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    update_dm_settings({"dm_filters_enabled": True})
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/openfilter - DM Filters Enabled", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, "✅ <b>DM Only Filters Enabled Globally</b>")

@bot.message_handler(commands=["closefilter"])
def close_dm_filter(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    update_dm_settings({"dm_filters_enabled": False})
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/closefilter - DM Filters Disabled", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, "❌ <b>DM Only Filters Disabled Globally</b>")

@bot.message_handler(commands=["enablefilter"])
def enable_dm_creation(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    update_dm_settings({"creation_mode": True})
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/enablefilter - Creation Mode Enabled", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, "🔧 <b>DM Only Creation Mode Enabled</b>")

@bot.message_handler(commands=["disablefilter"])
def disable_dm_creation(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    update_dm_settings({"creation_mode": False})
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/disablefilter - Creation Mode Disabled", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, "⚙️ <b>DM Only Creation Mode Disabled</b>")

@bot.message_handler(commands=["openglobalgroup"])
def open_global_groups(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    update_dm_settings({"global_groups_enabled": True})
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/openglobalgroup - Global Groups Enabled", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, "🌐 <b>DM Filters Enabled in All Groups</b>")

@bot.message_handler(commands=["closeglobalgroup"])
def close_global_groups(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    update_dm_settings({"global_groups_enabled": False})
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/closeglobalgroup - Global Groups Disabled", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, "🔒 <b>DM Filters Disabled in All Groups</b>")

@bot.message_handler(commands=["opengroup"])
def open_specific_group(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /opengroup <group_id>")
        return
    
    try:
        group_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid group ID!")
        return
    
    settings = get_dm_settings()
    enabled_groups = settings.get("enabled_groups", [])
    disabled_groups = settings.get("disabled_groups", [])
    
    # Remove from disabled groups if present
    if group_id in disabled_groups:
        disabled_groups.remove(group_id)
    
    # Add to enabled groups if not present
    if group_id not in enabled_groups:
        enabled_groups.append(group_id)
    
    update_dm_settings({
        "enabled_groups": enabled_groups,
        "disabled_groups": disabled_groups
    })
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/opengroup - Enabled DM Filters for Group {group_id}", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, f"✅ <b>DM Filters Enabled for Group</b>\n\nGroup ID: <code>{group_id}</code>")

@bot.message_handler(commands=["closegroup"])
def close_specific_group(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /closegroup <group_id>")
        return
    
    try:
        group_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid group ID!")
        return
    
    settings = get_dm_settings()
    enabled_groups = settings.get("enabled_groups", [])
    disabled_groups = settings.get("disabled_groups", [])
    
    # Remove from enabled groups if present
    if group_id in enabled_groups:
        enabled_groups.remove(group_id)
    
    # Add to disabled groups if not present
    if group_id not in disabled_groups:
        disabled_groups.append(group_id)
    
    update_dm_settings({
        "enabled_groups": enabled_groups,
        "disabled_groups": disabled_groups
    })
    
    # LOG ADMIN ACTION
    log_message("ADMIN_COMMAND", f"/closegroup - Disabled DM Filters for Group {group_id}", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    bot.reply_to(message, f"❌ <b>DM Filters Disabled for Group</b>\n\nGroup ID: <code>{group_id}</code>")

@bot.message_handler(commands=["closeid"])
def show_closed_groups(message: types.Message):
    """Show list of groups where DM filters are disabled"""
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Only admins can use this command!")
        return
    
    settings = get_dm_settings()
    disabled_groups = settings.get("disabled_groups", [])
    
    if not disabled_groups:
        bot.reply_to(message, "📭 No groups have DM filters disabled!")
        return
    
    # Try to get group names
    groups_info = []
    for group_id in disabled_groups:
        try:
            chat = bot.get_chat(group_id)
            group_name = chat.title or "Unknown Group"
            groups_info.append(f"• {group_name} - <code>{group_id}</code>")
        except Exception:
            groups_info.append(f"• Unknown Group - <code>{group_id}</code>")
    
    groups_list = "\n".join(groups_info)
    response = f"🔒 <b>Groups with DM Filters Disabled</b>\n\n{groups_list}\n\nTotal: <code>{len(disabled_groups)}</code> groups"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=["bfilters"])
def list_dm_filters(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "🔒 This command is for admins only!")
        return

    all_dm_filters = get_all_dm_filters()
    if not all_dm_filters:
        bot.reply_to(message, "📭 No DM only filters found!")
        return

    parts = message.text.split()
    if len(parts) > 1 and parts[1].lower() == "full":
        all_keys = "\n".join([f"- <code>{f.get('keyword','(no-keyword)')}</code>" for f in all_dm_filters])
        max_chunk = 3800
        if len(all_keys) > max_chunk:
            for i in range(0, len(all_keys), max_chunk):
                bot.reply_to(message, all_keys[i:i+max_chunk])
        else:
            bot.reply_to(message, f"📋 <b>DM Only Filters</b>:\n{all_keys}")
        return

    page_size = 10
    total_pages = (len(all_dm_filters) + page_size - 1) // page_size
    rows = []
    for fdata in all_dm_filters[:page_size]:
        display = short_display(fdata.get("keyword", ""), limit=50)
        # FIXED: Use dmfilter_ prefix for DM filters
        rows.append([types.InlineKeyboardButton(display, callback_data=f"dmfilter_{str(fdata.get('_id'))}")])
    
    if total_pages > 1:
        rows.append([types.InlineKeyboardButton("Next ➡️", callback_data="dmfilters_page_1")])
    
    # FIXED: Use show_dmfull_list for DM filters
    rows.append([types.InlineKeyboardButton("📜 Show Full List", callback_data="show_dmfull_list")])
    bot.reply_to(message, f"📋 DM Only Filters (Page 1/{total_pages}):", reply_markup=make_inline_keyboard(rows))

@bot.message_handler(commands=["fstatus"])
def dm_filters_status(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "🔒 This command is for admins only!")
        return
    
    settings = get_dm_settings()
    dm_filters_count = dm_filters_collection.count_documents({})
    
    status_msg = f"""🔧 <b>DM Filters Status</b>

📊 DM Only Filters: <code>{dm_filters_count}</code>

⚙️ <b>Settings:</b>
• Global DM Filters: <code>{'✅ Enabled' if settings['dm_filters_enabled'] else '❌ Disabled'}</code>
• Creation Mode: <code>{'🔧 DM Only' if settings['creation_mode'] else '⚙️ Normal'}</code>
• Global Groups: <code>{'🌐 All Groups' if settings['global_groups_enabled'] else '🔒 Disabled'}</code>
• Enabled Groups: <code>{len(settings.get('enabled_groups', []))}</code>
• Disabled Groups: <code>{len(settings.get('disabled_groups', []))}</code>"""

    bot.reply_to(message, status_msg)

# NEW: DM Filters Callback Handlers
@bot.callback_query_handler(func=lambda call: call.data.startswith('dmfilter_'))
def dm_filter_callback(call: types.CallbackQuery):
    """Handle DM filter selection from /bfilters"""
    filter_id = call.data.replace('dmfilter_', '')
    fdata = get_dm_filter_by_id(filter_id)
    
    if not fdata:
        bot.answer_callback_query(call.id, "DM Filter not found!", show_alert=True)
        return
    
    chat_id = call.message.chat.id
    try:
        if fdata["type"] == "text":
            bot.send_message(chat_id, fdata["data"])
        elif fdata["type"] == "photo":
            bot.send_photo(chat_id, fdata["file_id"], caption=fdata.get("caption", ""))
    except Exception:
        bot.answer_callback_query(call.id, "Failed to send DM filter.")
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "show_dmfull_list")
def show_dm_full_list(call: types.CallbackQuery):
    """Show full list of DM filters with proper chunking"""
    try:
        all_dm_filters = get_all_dm_filters()
        if not all_dm_filters:
            bot.answer_callback_query(call.id, "📭 No DM filters found!", show_alert=True)
            return
        
        # Create the full list text
        all_keys = "\n".join([f"- <code>{f.get('keyword','(no-keyword)')}</code>" for f in all_dm_filters])
        total_filters = len(all_dm_filters)
        
        # Send with proper chunking
        max_chunk = 3800  # Telegram limit se thoda kam
        header = f"📋 <b>All DM Only Filters</b> (Total: {total_filters}):\n\n"
        
        if len(header + all_keys) <= max_chunk:
            # Ek message mein fit ho jaye toh
            bot.send_message(call.message.chat.id, header + all_keys)
        else:
            # Multiple messages mein send karo
            # Pehle header bhejo
            bot.send_message(call.message.chat.id, header)
            
            # Ab filters ko chunks mein send karo
            current_chunk = ""
            for i, filter_text in enumerate(all_keys.split('\n')):
                if len(current_chunk + filter_text + '\n') > max_chunk:
                    # Current chunk send karo
                    if current_chunk:
                        bot.send_message(call.message.chat.id, current_chunk)
                    current_chunk = filter_text + '\n'
                else:
                    current_chunk += filter_text + '\n'
            
            # Last chunk send karo
            if current_chunk:
                bot.send_message(call.message.chat.id, current_chunk)
        
        bot.answer_callback_query(call.id, f"✅ Sent {total_filters} DM filters!")
        
    except Exception as e:
        logger.exception("show_dm_full_list failed: %s", e)
        try:
            bot.answer_callback_query(call.id, "❌ Failed to send DM filters list.", show_alert=True)
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("dmfilters_page_"))
def dm_filters_pagination(call: types.CallbackQuery):
    """DM filters pagination"""
    try:
        page = int(call.data.replace("dmfilters_page_", ""))
    except ValueError:
        bot.answer_callback_query(call.id, "Invalid page!")
        return
    
    all_dm_filters = get_all_dm_filters()
    page_size = 10
    total_pages = (len(all_dm_filters) + page_size - 1) // page_size
    start_idx = page * page_size
    end_idx = start_idx + page_size
    
    rows = []
    for fdata in all_dm_filters[start_idx:end_idx]:
        display = short_display(fdata.get("keyword",""), limit=50)
        rows.append([types.InlineKeyboardButton(display, callback_data=f"dmfilter_{str(fdata.get('_id'))}")])
    
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"dmfilters_page_{page - 1}"))
    if end_idx < len(all_dm_filters):
        nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"dmfilters_page_{page + 1}"))
    if nav:
        rows.append(nav)
    
    rows.append([types.InlineKeyboardButton("📜 Show Full List", callback_data="show_dmfull_list")])
    
    try:
        bot.edit_message_text(f"📋 DM Only Filters (Page {page + 1}/{total_pages}):", 
                            call.message.chat.id, call.message.message_id, 
                            reply_markup=make_inline_keyboard(rows))
        bot.answer_callback_query(call.id)
    except Exception:
        bot.answer_callback_query(call.id, "Unable to paginate.")

# ORIGINAL CODE STARTS HERE (NO CHANGES)

# /start
@bot.message_handler(commands=["start"])
def start_handler(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) > 1 and parts[1] == "anime_keyboard":
            anime_keyboard_handler_private(message)
            return
    except Exception:
        pass

    name = message.from_user.first_name if message.from_user else "User"
    user_id = message.from_user.id if message.from_user else message.chat.id
    chat_id = message.chat.id

    update_user_data(user_id, chat_id)

    # LOG NEW USER/GROUP
    if message.chat.type == "private":
        log_message("NEW_USER", f"User started the bot", 
                    user_id, chat_id,
                    message.from_user.username if message.from_user else None,
                    name,
                    None)
    else:
        log_message("NEW_GROUP", f"Bot added to group", 
                    user_id, chat_id,
                    message.from_user.username if message.from_user else None,
                    name,
                    message.chat.title if message.chat.title else None)

    caption = f"""👋 𝐇𝐞𝐲, {name}!
🆔 𝐘𝐨𝐮𝐫 𝐈𝐃: <code>{user_id}</code>

<blockquote>» ᴛʜᴀɴᴋ ʏᴏᴜ! ꜰᴏʀ ᴜꜱɪɴɢ ᴍᴇ. ɪ ᴄᴀɴ ᴘʀᴏᴠɪᴅᴇ ᴀɴɪᴍᴇꜱ ꜰɪʟᴇꜱ. ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ ꜰɪʟᴇꜱ ᴠɪᴀ ᴛʜɪꜱ ᴄʜᴀɴɴᴇʟ.

○ 𝐇ɪɴᴅɪ 𝐃ᴜ𝐛 𝐀ɴɪᴍᴇ : <a href="https://t.me/Infinity_anime_Station">𝐈ɴғɪɴɪᴛʏ 𝐀ɴɪᴍᴇ</a>
○ 𝐀ɴɪᴍᴇ ᴍᴏᴠɪᴇs 𝐀ɴ𝐝 𝐒ᴇʀɪᴇꜱ : <a href="https://t.me/Infinity_Anime_Movies">𝐌ᴏᴠɪᴇs & 𝐒ᴇʀɪᴇs</a>
○ 𝐀ɴɪᴍᴇ 𝐍ᴇᴡs : <a href="https://t.me/+G-OJ0Yjayk84Y2M1">𝐍ᴇᴡ𝐬</a>

💡 ᴛɪᴘ: ᴛᴀᴘ 'ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ' ᴛᴏ ᴇxᴘʟᴏʀᴇ ᴀʟʟ ꜰᴇᴀᴛᴜʀᴇꜱ 🛠️</blockquote>"""

    buttons = [
        [types.InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url="https://t.me/Roxy_Anime_FilterBot?startgroup=true")],
        [types.InlineKeyboardButton("ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help")],
        [
            types.InlineKeyboardButton("Group", url="https://t.me/+Rfw4uDK0YhkxNGNl"),
            types.InlineKeyboardButton("Movies", url="https://t.me/Infinity_Anime_Movies")
        ],
        [types.InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ", url="https://t.me/Infinity_anime_Station")]
    ]

    try:
        bot.send_photo(
            chat_id=message.chat.id,
            photo="https://graph.org/file/161b2d3bc949d64159540-8591272c4ef191036b.jpg",
            caption=caption,
            reply_markup=make_inline_keyboard(buttons),
            message_effect_id="5104841245755180586",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.exception("start_handler send_photo failed: %s", e)
        bot.send_message(message.chat.id, caption, parse_mode="HTML", reply_markup=make_inline_keyboard(buttons))
        
#CMD COMMAND 

@bot.message_handler(commands=["cmd"])
def cmd_handler(message: types.Message):

    name = message.from_user.first_name if message.from_user else "User"
    user_id = message.from_user.id if message.from_user else message.chat.id

    # LOG COMMAND USAGE
    log_message("COMMAND_USED", f"/cmd - Command list accessed", 
                user_id, message.chat.id,
                message.from_user.username if message.from_user else None,
                name,
                message.chat.title if message.chat.title else None)

    caption = f"""👋 𝐇𝐞𝐲, {name}!
🆔 𝐘𝐨𝐮𝐫 𝐈𝐃: <code>{user_id}</code>

<blockquote>»ᴄᴍᴅ ᴄᴏᴍᴍᴀɴᴅ
ᴄᴏᴍᴘʟᴇᴛᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ ɢᴜɪᴅᴇ

<b>ᴡʜᴀᴛ ɪᴛ ᴄᴏɴᴛᴀɪɴꜱ:</b>
• ᴀʟʟ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ ᴄᴀᴛᴇɢᴏʀɪᴢᴇᴅ
• ᴅᴇᴛᴀɪʟᴇᴅ ᴜꜱᴀɴɢᴇ ɪɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ
• ʙᴜᴛᴛᴏɴ-ʙᴀꜱᴇᴅ ɴᴀᴠɪɢᴀᴛɪᴏɴ
• ꜱᴜʙ-ᴄᴀᴛᴇɢᴏʀɪᴇꜱ ꜰᴏʀ ᴇᴀꜱʏ ᴀᴄᴄᴇꜱꜱ

<b>ᴡʜʏ ɪᴛ ᴡᴀꜱ ᴄʀᴇᴀᴛᴇᴅ:</b>
ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄᴏᴍᴘʟᴇᴛᴇ ᴀɴᴅ ᴀᴅᴍɪɴ-ꜰʀɪᴇɴᴅʟʏ ɢᴜɪᴅᴇ ꜰᴏʀ ᴀʟʟ ʙᴏᴛ ꜰᴇᴀᴛᴜʀᴇꜱ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅꜱ</blockquote>"""

    buttons = [
        [
            types.InlineKeyboardButton("ꜰɪʟᴛᴇʀ", callback_data="ffilter_help"),
            types.InlineKeyboardButton("ᴅᴍꜰɪʟᴛᴇʀ", callback_data="dmffilter_help"),
            types.InlineKeyboardButton("fstatus", callback_data="fstatus_help"),
        ],
        [
            types.InlineKeyboardButton("ꜱᴛᴀᴛꜱ", callback_data="sstats_help"),
            types.InlineKeyboardButton("ʙʀᴏᴀᴅᴄᴀꜱᴛ!!", callback_data="bbroadcast_help"),
            types.InlineKeyboardButton("ᴘɪɴɢ", callback_data="pping_help"),
        ],
        [
            types.InlineKeyboardButton("fstats", callback_data="fstats_help")

        ],
    ]

    try:
        bot.send_photo(
            chat_id=message.chat.id,
            photo="https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg",
            caption=caption,
            reply_markup=make_inline_keyboard(buttons),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.exception("start_handler send_photo failed: %s", e)
        bot.send_message(message.chat.id, caption, parse_mode="HTML", reply_markup=make_inline_keyboard(buttons))
#CMD STOPP

# callback dispatcher (fixed)
@bot.callback_query_handler(func=lambda call: True)
def callback_dispatcher(call: types.CallbackQuery):
    data = call.data or ""

    # Handle DM filters callbacks first
    if data.startswith('dmfilter_'):
        dm_filter_callback(call)
        return
    elif data == "show_dmfull_list":
        show_dm_full_list(call)
        return
    elif data.startswith("dmfilters_page_"):
        dm_filters_pagination(call)
        return

    # HELP
    if data == "help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote>➪ ɪ ᴀᴍ ᴛʜᴇ ꜰᴀꜱᴛᴇꜱᴛ ᴀɴɪꜰɪʟᴛᴇʀ ʙᴏᴛ ᴛᴏ ꜰɪɴᴅ ʜɪɴᴅɪ ᴅᴜʙʙᴇᴅ ᴀɴɪᴍᴇꜱ, ᴍᴏᴠɪᴇꜱ & ꜱᴇʀɪᴇꜱ.
➪ ᴊᴜꜱᴛ ᴛʏᴘᴇ ᴛʜᴇ ɴᴀᴍᴇ — ʏᴏᴜ'ʟʟ ɢᴇᴛ ɪɴꜱᴛᴀɴᴛ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋꜱ.
🔍 ᴍᴀᴋᴇ ꜱᴜʀᴇ ɴᴀᴍᴇ ɪꜱ ᴄᴏʀʀᴇᴄᴛ & ʜɪɴᴅɪ ᴅᴜʙʙᴇᴅ ᴇxɪꜱᴛꜱ.
➪ ꜰᴏʀ ᴍᴏʀᴇ ʜᴇʟᴘ, ᴊᴏɪɴ ᴛʜᴇ ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ʙᴇʟᴏᴡ.

◈ ◈ ᴛɪᴘ: ɪꜰ ʏᴏᴜ ᴛʏᴘᴇ #ᴀɴɪᴍᴇ ɪɴ ᴅᴍ ᴏʀ ɢʀᴏᴜᴘ, ʏᴏᴜ'ʟʟ ɢᴇᴛ ᴀ ᴋᴇʏʙᴏᴀʀᴅ.
ᴊᴜꜱᴛ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ꜰɪʀꜱᴛ ᴡᴏʀᴅ ᴏꜰ ʏᴏᴜʀ ᴅᴇꜱɪʀᴇᴅ ᴀɴɪᴍᴇ.
ɪꜰ ɴᴏᴛ ꜰᴏᴜɴᴅ, ᴛᴀᴘ ᴏɴ (ᴏᴛʜᴇʀ).</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton("💞Support Group ", url="https://t.me/+Rfw4uDK0YhkxNGNl"),
            types.InlineKeyboardButton("👨‍💻 Developer ", url="https://t.me/@MrSumit09")
        )
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_start"))
        
        try:
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/97029e53268bd23b76150-da705c2a86f93e8273.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    message_effect_id="5104841245755180586",
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open help.", show_alert=False)
        return

    # BACK TO START
    if data == "back_to_start":
        name = call.from_user.first_name if call.from_user else "User"
        user_id = call.from_user.id if call.from_user else call.message.chat.id

        caption = f"""👋 𝐇𝐞𝐲, {name}!
🆔 𝐘𝐨𝐮𝐫 𝐈𝐃: <code>{user_id}</code>

<blockquote>» ᴛʜᴀɴᴋ ʏᴏᴜ! ꜰᴏʀ ᴜꜱɪɴɢ ᴍᴇ. ɪ ᴄᴀɴ ᴘʀᴏᴠɪᴅᴇ ᴀɴɪᴍᴇꜱ ꜰɪʟᴇꜱ. ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ ꜰɪʟᴇꜱ ᴠɪᴀ ᴛʜɪꜱ ᴄʜᴀɴɴᴇʟ.

○ 𝐇ɪɴᴅɪ 𝐃ᴜ𝐛 𝐀ɴɪᴍᴇ : <a href="https://t.me/Infinity_anime_Station">𝐈ɴғɪɴɪᴛʏ 𝐀ɴɪᴍᴇ</a>
○ 𝐀ɴɪᴍᴇ ᴍᴏᴠɪᴇs 𝐀ɴ𝐝 𝐒ᴇʀɪᴇꜱ : <a href="https://t.me/Infinity_Anime_Movies">𝐌ᴏᴠɪᴇs & 𝐒ᴇʀɪᴇs</a>
○ 𝐀ɴɪᴍᴇ 𝐍ᴇᴡs : <a href="https://t.me/+G-OJ0Yjayk84Y2M1">𝐍ᴇᴡ𝐬</a>

💡 ᴛɪᴘ: ᴛᴀᴘ 'ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ' ᴛᴏ ᴇxᴘʟᴏʀᴇ ᴀʟʟ ꜰᴇᴀᴛᴜʀᴇꜱ 🛠️</blockquote>"""

        buttons = [
            [types.InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url="https://t.me/Roxy_Anime_FilterBot?startgroup=true")],
            [types.InlineKeyboardButton("ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help")],
            [
                types.InlineKeyboardButton("Group", url="https://t.me/+Rfw4uDK0YhkxNGNl"),
                types.InlineKeyboardButton("Movies", url="https://t.me/Infinity_Anime_Movies")
            ],
            [types.InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ", url="https://t.me/Infinity_anime_Station")]
        ]
        
        try:
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/161b2d3bc949d64159540-8591272c4ef191036b.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=make_inline_keyboard(buttons)
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=caption,
                    reply_markup=make_inline_keyboard(buttons),
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    caption,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=make_inline_keyboard(buttons),
                    message_effect_id="5104841245755180586",
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("back_to_start edit failed: %s", e)
            try:
                bot.edit_message_text(
                    caption,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=make_inline_keyboard(buttons),                
                    parse_mode="HTML"
                )
                bot.answer_callback_query(call.id)
            except Exception as e2:
                logger.exception("back_to_start: fallback edit_text failed: %s", e2)
                bot.answer_callback_query(call.id, "Unable to go back to start.", show_alert=False)

#CMD COMMAND 

# callback dispatcher (fixed)

    # ffilter_help
    elif data == "ffilter_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote>➪ꜰɪʟᴛᴇʀ
ᴀᴅᴅ ꜰɪʟᴛᴇʀ:
<code>/filter</code> ᴋᴇʏᴡᴏʀᴅ - ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ
ʏᴏᴜ ᴄᴀɴ ᴀᴅᴅ ꜰɪʟᴛᴇʀꜱ ɪɴ ɢʀᴏᴜᴘ ᴀɴᴅ ᴅᴍ ʙᴏᴛʜ

ꜱᴛᴏᴘ ꜰɪʟᴛᴇʀ:
<code>/stop</code> ᴋᴇʏᴡᴏʀᴅ - ᴅᴇʟᴇᴛᴇ ᴀ ꜰɪʟᴛᴇʀ
ʏᴏᴜ ᴄᴀɴ ꜱᴛᴏᴘ ꜰɪʟᴛᴇʀꜱ ɪɴ ɢʀᴏᴜᴘ ᴀɴᴅ ᴅᴍ ʙᴏᴛʜ

ᴀʟʟ ꜰɪʟᴛᴇʀꜱ:
<code>/filters</code> - ꜱʜᴏᴡ ᴀʟʟ ꜱᴀᴠᴇᴅ ꜰɪʟᴛᴇʀꜱ</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("ffilter_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open ffilter_help.", show_alert=False)
        return
        
    # Callback dmffilter_help

    # dmffilter_help
    elif data == "dmffilter_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>➪ᴅᴍ ꜰɪʟᴛᴇʀ</b>
ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀ ᴀᴅᴅ:
<code>/filter</code> ᴋᴇʏᴡᴏʀᴅ - ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ
ʏᴏᴜ ᴄᴀɴ ᴀᴅᴅ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɪɴ ɢʀᴏᴜᴘ ᴀɴᴅ ᴅᴍ ʙᴏᴛʜ

ꜱᴛᴏᴘ ᴅᴍ ꜰɪʟᴛᴇʀ:
<code>/stop</code> ᴋᴇʏᴡᴏʀᴅ - ᴅᴇʟᴇᴛᴇ ᴀ ᴅᴍ ꜰɪʟᴛᴇʀ
ʏᴏᴜ ᴄᴀɴ ꜱᴛᴏᴘ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɪɴ ɢʀᴏᴜᴘ ᴀɴᴅ ᴅᴍ ʙᴏᴛʜ

ᴀʟʟ ᴅᴍ ꜰɪʟᴛᴇʀꜱ:
<code>/bfilters</code> - ꜱʜᴏᴡ ᴀʟʟ ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ

ɴᴏᴛᴇ:
ᴛᴏ ᴜꜱᴇ ᴅᴍ ꜰɪʟᴛᴇʀꜱ, ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ɢᴏ ʙᴀᴄᴋ ᴀɴᴅ ᴄʜᴇᴄᴋ ꜰꜱᴛᴀᴛᴜꜱ ꜰᴏʀ ꜰᴜʟʟ ꜰᴇᴀᴛᴜʀᴇꜱ ᴛᴏ ꜱᴇᴇ ʜᴏᴡ ᴛᴏ ᴜꜱᴇ ᴛʜᴇᴍ ᴀɴᴅ ʜᴏᴡ ᴛᴏ ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪꜱᴀʙʟᴇ ᴛʜᴇᴍ
</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("dmffilter_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open dmffilter_help.", show_alert=False)
        return

    # fstatus_help
    elif data == "fstatus_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>➪ꜰꜱᴛᴀᴛᴜꜱ</b>
<code>/fstatus</code>- ꜱʜᴏᴡꜱ ᴄᴏᴍᴘʟᴇᴛᴇ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ʀᴇᴘᴏʀᴇ:
• ɢʟᴏʙᴀʟ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜱᴛᴀᴛᴜꜱ (ᴇɴᴀʙʟᴇᴅ/ᴅɪꜱᴀʙʟᴇᴅ)
• ᴄʀᴇᴀᴛɪᴏɴ ᴍᴏᴅᴇ ꜱᴛᴀᴛᴜꜱ (ᴅᴍ ᴏɴʟʏ/ɴᴏʀᴍᴀʟ)
• ɢʟᴏʙᴀʟ ɢʀᴏᴜᴘꜱ ꜱᴛᴀᴛᴜꜱ (ᴇɴᴀʙʟᴇᴅ/ᴅɪꜱᴀʙʟᴇᴅ)
• ᴇɴᴀʙʟᴇᴅ ɢʟᴏᴜᴘꜱ ᴄᴏᴜɴᴛ
• ᴅɪꜱᴀʙʟᴇᴅ ɢʀᴏᴜᴘꜱ ᴄᴏᴜɴᴛ
• ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ ᴄᴏᴜɴᴛ</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("fstatus_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open fstatus_help.", show_alert=False)
        return
                
# callback dispatcher (fixed)

    # sstats_help
    elif data == "sstats_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote>➪<b>ꜱᴛᴀᴛꜱ</b>
<code>/stats</code> - ꜱʜᴏᴡꜱ ᴄᴏᴍᴘʟᴇᴛᴇ ʙᴏᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ:
• ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ ᴄᴏᴜɴᴛ
• ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘꜱ ᴄᴏᴜɴᴛ
• ᴛᴏᴛᴀʟ ɴᴏʀᴍᴀʟ ꜰɪʟᴛᴇʀꜱ ᴄᴏᴜɴᴛ
• ᴛᴏᴛᴀʟ ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ ᴄᴏᴜɴᴛ
• ᴀᴅᴍɪɴꜱ ʟɪꜱᴛ
• ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("sstats_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open sstats_help.", show_alert=False)
        return

# callback dispatcher (fixed)


    # bbroadcast_help
    elif data == "bbroadcast_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote expendable>➪<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ</b>
<code>/broadcast</>- ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ꜱᴇɴᴅ ɪᴛ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀꜱ ᴀɴᴅ ɢʀᴏᴜᴘꜱ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
1. ꜱᴇɴᴅ ᴀ ᴍᴇꜱꜱᴀɢᴇ (ᴛᴇxᴛ/ᴘʜᴏᴛᴏ/ᴀɴʏ ᴛʏᴘᴇ)
2. ʀᴇᴘʟʏ ᴛᴏ ɪᴛ ᴡɪᴛʜ /ʙʀᴏᴀᴅᴄᴀꜱᴛ
3. ʙᴏᴛ ᴡɪʟʟ ꜱᴇɴᴅ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀꜱ ᴀɴᴅ ɢʀᴏᴜᴘꜱ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ
4. ꜱʜᴏᴡꜱ ᴘʀᴏɢʀᴇꜱꜱ ᴡɪᴛʜ ꜱᴜᴄᴄᴇꜱꜱ/ꜰᴀɪʟᴇᴅ ᴄᴏᴜɴᴛꜱ

➪<b>ᴀʙʀᴏᴀᴅᴄᴀꜱᴛ</b>
<code>/abroadcast</code>- ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ꜱᴇɴᴅ ɪᴛ ᴏɴʟʏ ᴛᴏ ᴀᴅᴍɪɴꜱ ɪɴ ᴅᴍ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
1. ꜱᴇɴᴅ ᴀ ᴍᴇꜱꜱᴀɢᴇ (ᴛᴇxᴛ/ᴘʜᴏᴛᴏ/ᴀɴʏ ᴛʏᴘᴇ)
2. ʀᴇᴘʟʏ ᴛᴏ ɪᴛ ᴡɪᴛʜ /ᴀʙʀᴏᴀᴅᴄᴀꜱᴛ
3. ʙᴏᴛ ᴡɪʟʟ ꜱᴇɴᴅ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴏɴʟʏ ᴛᴏ ᴀʟʟ ᴀᴅᴍɪɴꜱ ɪɴ ᴅᴍ
4. ɢʀᴏᴜᴘꜱ ᴀʀᴇ ᴄᴏᴍᴘʟᴇᴛᴇʟʏ ᴇxᴄʟᴜᴅᴇᴅ
5. ꜱʜᴏᴡꜱ ᴘʀᴏɢʀᴇꜱꜱ ᴡɪᴛʜ ꜱᴜᴄᴄᴇꜱꜱ/ꜰᴀɪʟᴇᴅ ᴄᴏᴜɴᴛꜱ</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("bbroadcast_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open bbroadcast_help.", show_alert=False)
        return
  
# callback dispatcher (fixed)

    # pping_help
    elif data == "pping_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote>➪<b>ᴘɪɴɢ</b>
<code>/ping</code> - ᴄʜᴇᴄᴋꜱ ʙᴏᴛ'ꜱ ʀᴇꜱᴘᴏɴꜱᴇ ᴛɪᴍᴇ ᴀɴᴅ ꜱᴛᴀᴛᴜꜱ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ꜱᴇɴᴅꜱ ᴀ ʀᴇꜱᴘᴏɴꜱᴇ ᴡɪᴛʜ "ᴘᴏɴɢ!"
• ꜱʜᴏᴡꜱ ʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ᴀɴᴅ ᴡᴏʀᴋɪɴɢ
• ᴍᴇᴀꜱᴜʀᴇꜱ ʀᴇꜱᴘᴏɴꜱᴇ ᴛɪᴍᴇ
• ᴄᴏɴꜰɪʀᴍꜱ ʙᴏᴛ ᴄᴏɴɴᴇᴄᴛɪᴠɪᴛʏ

ᴏᴜᴛᴘᴜᴛ:
"ᴘᴏɴɢ! ʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ᴀɴᴅ ᴡᴏʀᴋɪɴɢ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b3b8833bc42827b420d82-0ffb1a06ba804d18ef.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("pping_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open pping_help.", show_alert=False)
        return
                      
# callback dispatcher (fixed)

    # fstats_help
    elif data == "fstats_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote>➪<b>ꜱᴛᴀᴛꜱ</b>
<code>/fstats</code> - ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɢɪᴠᴇꜱ ʏᴏᴜ ᴀʟʟ ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ ꜰᴇᴀᴛᴜʀᴇꜱ ᴀɴᴅ ꜱᴇᴛᴛɪɴɢꜱ. ʙᴇʟᴏᴡ ʏᴏᴜ ᴄᴀɴ ꜱᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ ᴀɴᴅ ᴛʜᴇɪʀ ᴜꜱᴇꜱ.</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton("enable", callback_data="enable_help"),
            types.InlineKeyboardButton("disable", callback_data="disable_help"),
            types.InlineKeyboardButton("open", callback_data="open_help")
        )
        kb.row(types.InlineKeyboardButton("close", callback_data="close_help"),
            types.InlineKeyboardButton("openglobal", callback_data="openglobal_help"),
            types.InlineKeyboardButton("closeglobal", callback_data="closeglobal_help")
        )
        kb.row(
            types.InlineKeyboardButton("opengroup", callback_data="opengroup_help"),
            types.InlineKeyboardButton("closegroup", callback_data="closegroup_help"),
            types.InlineKeyboardButton("closeid", callback_data="closeid_help")
        )
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))
        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("fstats_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open fstats_help.", show_alert=False)
        return
        
      
    # enablfilter_help
    elif data == "enable_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>➪ᴇɴᴀʙʟᴇꜰɪʟᴛᴇʀ</b>
<code>/enablefilter</code>- ᴛᴜʀɴꜱ ᴏɴ ᴅᴍ ᴏɴʟʏ ᴄʀᴇᴀᴛɪᴏɴ ᴍᴏᴅᴇ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ᴡʜᴇɴ ᴇɴᴀʙʟᴇᴅ, ᴀʟʟ ɴᴇᴡ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ʙᴇ ꜱᴀᴠᴇᴅ ᴀꜱ ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ
• ɴᴏʀᴍᴀʟ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ɴᴏᴛ ʙᴇ ᴄʀᴇᴀᴛᴇᴅ
• ᴏɴʟʏ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ʀᴇꜱᴘᴏɴᴅ ᴛᴏ ᴋᴇʏᴡᴏʀᴅꜱ
• ᴜꜱᴇ /ᴅɪꜱᴀʙʟᴇꜰɪʟᴛᴇʀ ᴛᴏ ᴛᴜʀɴ ᴏꜰꜰ

ᴇꜰꜰᴇᴄᴛ: ᴄᴏɴᴛʀᴏʟꜱ ᴡʜᴇʀᴇ ɴᴇᴡ ꜰɪʟᴛᴇʀꜱ ᴀʀᴇ ꜱᴀᴠᴇᴅ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("enable_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open enable_help.", show_alert=False)
        return
        
    # disablfilter_help
    elif data == "disable_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>➪ᴅɪꜱᴀʙʟᴇ ꜰɪʟᴛᴇʀ</b>
<code>/disablefilter</code>- ᴛᴜʀɴꜱ ᴏꜰꜰ ᴅᴍ ᴏɴʟʢ ᴄʀᴇᴀᴛɪᴏɴ ᴍᴏᴅᴇ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ꜱᴡɪᴛᴄʜᴇꜱ ᴄʀᴇᴀᴛɪᴏɴ ᴍᴏᴅᴇ ᴛᴏ ɴᴏʀᴍᴀʟ
• ɴᴇᴡ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ʙᴇ ꜱᴀᴠᴇᴅ ᴀꜱ ɴᴏʀᴍᴀʟ ꜰɪʟᴛᴇʀꜱ
• ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀ ᴄʀᴇᴀᴛɪᴏɴ ɪꜱ ᴅɪꜱᴀʙʟᴇᴅ

ᴇꜰꜰᴇᴄᴛ: ᴄᴏɴᴛʀᴏʟꜱ ᴡʜᴇʀᴇ ɴᴇᴡ ꜰɪʟᴛᴇʀꜱ ᴀʀᴇ ꜱᴀᴠᴇᴅ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("disable_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open disable_help.", show_alert=False)
        return
        
    # open_help
    elif data == "open_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>ᴏᴘᴇɴ ꜰɪʟᴛᴇʀ</b>
<code>/openfilter</code> - ᴇɴᴀʙʟᴇꜱ ɢʟᴏʙᴀʟ ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ᴛᴜʀɴꜱ ᴏɴ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɢʟᴏʙᴀʟʟʏ
• ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ʀᴇꜱᴘᴏɴᴅ ᴛᴏ ᴋᴇʏᴡᴏʀᴅꜱ
• ᴡᴏʀᴋꜱ ɪɴ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛꜱ ᴀɴᴅ ᴇɴᴀʙʟᴇᴅ ɢʀᴏᴜᴘꜱ

ᴇꜰꜰᴇᴄᴛ: ᴄᴏɴᴛʀᴏʟꜱ ᴇɴᴛɪʀᴇ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜱʏꜱᴛᴇᴍ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("open_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open open_help.", show_alert=False)
        return
        
    # close_help
    elif data == "close_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>ᴄʟᴏꜱᴇ ꜰɪʟᴛᴇʀ</b>
<code>/closefilter</code>- ᴅɪꜱᴀʙʟᴇꜱ ɢʟᴏʙᴀʟ ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ᴛᴜʀɴꜱ ᴏꜰꜰ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɢʟᴏʙᴀʟʟʏ
• ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ɴᴏᴛ ʀᴇꜱᴘᴏɴᴅ ᴛᴏ ᴋᴇʙᴡᴏʀᴅꜱ
• ᴄᴏᴍᴘʟᴇᴛᴇ ꜱʏꜱᴛᴇᴍ ɪꜱ ᴅɪꜱᴀʙʟᴇᴅ

ᴇꜰꜰᴇᴄᴛ: ᴄᴏᴍᴘʟᴇᴛᴇʟʏ ᴅɪꜱᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜱʏꜱᴛᴇᴍ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("close_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open close_help.", show_alert=False)
        return
            
    # openglobal_help
    elif data == "openglobal_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>ᴏᴘᴇɴ ɢʟᴏʙᴀʟ ɢʀᴏᴜᴘ</b>
<code>/openglobalgroup</code>- ᴇɴᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɪɴ ᴀʟʟ ɢʀᴏᴜᴘꜱ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ᴡᴏʀᴋ ɪɴ ᴇᴠᴇʀʏ ɢʀᴏᴜᴘ
• ᴄᴀɴ ᴅɪꜱᴀʙʟᴇ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘꜱ ᴡɪᴛʜ /ᴄʟᴏꜱᴇɢʀᴏᴜᴘ
• ɢʟᴏʙᴀʟ ɢʀᴏᴜᴘ ᴀᴄᴄᴇꜱꜱ ꜰᴏʀ ᴅᴍ ꜰɪʟᴛᴇʀꜱ

ᴇꜰꜰᴇᴄᴛ: ᴇɴᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɪɴ ᴀʟʟ ɢʟᴏᴜᴘꜱ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("openglobal_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open openglobal_help.", show_alert=False)
        return
        
    # closeglobal_help
    elif data == "closeglobal_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>ᴄʟᴏꜱᴇ ɢʟᴏʙᴀʟ ɢʀᴏᴜᴘ</b>
<code>/closeglobalgroup</code>- ᴅɪꜱᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɪɴ ᴀʟʟ ɢʀᴏᴜᴘꜱ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴅɪꜱᴀʙʟᴇᴅ ɪɴ ᴀʟʟ ɢʀᴏᴜᴘꜱ
• ᴄᴀɴ ᴇɴᴀʙʟᴇ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘꜱ ᴡɪᴛʜ /ᴏᴘᴇɴɢʀᴏᴜᴘ
• ɢʟᴏʙᴀʟ ɢʀᴏᴜᴘ ᴀᴄᴄᴇꜱꜱ ʀᴇᴍᴏᴠᴇᴅ

ᴇꜰꜱᴇᴄᴛ: ᴅɪꜱᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ɪɴ ᴀʟʟ ɢʀᴏᴜᴘꜱ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("closeglobal_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open closeglobal_help.", show_alert=False)
        return
        
    # opengroup_help
    elif data == "opengroup_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>ᴏᴘᴇɴ ɢʀᴏᴜᴘ</b>
<code>/opengroup</code> ɢʀᴏᴜᴘ_ɪᴅ - ᴇɴᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜰᴏʀ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ᴇɴᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜰᴏʀ ᴛʜᴇ ꜱᴘᴇᴄɪꜰɪᴇᴅ ɢʀᴏᴜᴘ ɪᴅ
• ᴇxᴀᴍᴘʟᴇ: /ᴏᴘᴇɴɢʀᴏᴜᴘ -100123456789
• ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ᴡᴏʀᴋ ɪɴ ᴛʜᴀᴛ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘ

ᴇꜰꜰᴇᴄᴛ: ᴇɴᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜰᴏʀ ᴀ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘ ᴏɴʟʏ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("opengroup_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open opengroup_help.", show_alert=False)
        return
        
    # closegroup_help
    elif data == "closegroup_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>ᴄʟᴏꜱᴇ ɢʀᴏᴜᴘ</b>
<code>/closegroup</code> ɢʀᴏᴜᴘ_ɪᴅ - ᴅɪꜱᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜰᴏʀ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ᴅɪꜱᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜰᴏʀ ᴛʜᴇ ꜱᴘᴇᴄɪꜰɪᴇᴅ ɢʀᴏᴜᴘ ɪᴅ
• ᴇxᴀᴍᴘʟᴇ: /ᴄʟᴏꜱᴇɢʀᴏᴜᴘ -100123456789
• ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴡɪʟʟ ɴᴏᴛ ᴡᴏʀᴋ ɪɴ ᴛʜᴀᴛ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘ

ᴇꜰꜰᴇᴄᴛ: ᴅɪꜱᴀʙʟᴇꜱ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ꜰᴏʀ ᴀ ꜱᴘᴇᴄɪꜰɪᴄ ɢʀᴏᴜᴘ ᴏɴʟʏ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("closegroup_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open closegroup_help.", show_alert=False)
        return
        
    # closeid_help
    elif data == "closeid_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote><b>ᴄʟᴏꜱᴇɪᴅ</b>
<code>/closeid</code> - ꜱʜᴏᴡꜱ ʟɪꜱᴛ ᴏꜰ ɢʀᴏᴜᴘꜱ ᴡʜᴇʀᴇ ᴅᴍ ꜰɪʟᴛᴇʀꜱ ᴀʀᴇ ᴅɪꜱᴀʙʟᴇᴅ

ʜᴏᴡ ɪᴛ ᴡᴏʀᴋꜱ:
• ꜱʜᴏᴡꜱ ɢʀᴏᴜᴘ ɴᴀᴍᴇꜱ ᴀɴᴅ ɪᴅꜱ
• ᴅɪꜱᴘʟᴀʏꜱ ᴀʟʟ ɢʀᴏᴜᴘꜱ ᴡɪᴛʜ ᴅɪꜱᴀʙʟᴇᴅ ᴅᴍ ꜰɪʟᴛᴇʀꜱ
• ꜱʜᴏᴡꜱ ᴛᴏᴛᴀʟ ᴄᴏᴜɴᴛ ᴏꜰ ᴅɪꜱᴀʙʟᴇᴅ ɢʀᴏᴜᴘꜱ

ᴇꜰꜰᴇᴄᴛ: ᴘʀᴏᴠɪᴅᴇꜱ ᴄᴏᴍᴘʟᴇᴛᴇ ʟɪꜱᴛ ᴏꜰ ɢʀᴏᴜᴘꜱ ᴡɪᴛʜ ᴅɪꜱᴀʙʟᴇᴅ ᴅᴍ ꜰɪʟᴛᴇʀꜱ"</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_fstats_help"))

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("closeid_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open closeid_help.", show_alert=False)
        return
        
    # BACK TO FSTATS
        # fstats_help
    if data == "back_to_fstats_help":
        help_text = """💞 Hᴇʏ...!!,

<blockquote>➪<b>ꜱᴛᴀᴛꜱ</b>
<code>/fstats</code> - ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɢɪᴠᴇꜱ ʏᴏᴜ ᴀʟʟ ᴅᴍ ᴏɴʟʏ ꜰɪʟᴛᴇʀꜱ ꜰᴇᴀᴛᴜʀᴇꜱ ᴀɴᴅ ꜱᴇᴛᴛɪɴɢꜱ. ʙᴇʟᴏᴡ ʏᴏᴜ ᴄᴀɴ ꜱᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ ᴀɴᴅ ᴛʜᴇɪʀ ᴜꜱᴇꜱ.</blockquote>"""

        kb = types.InlineKeyboardMarkup()
        kb.row(
            types.InlineKeyboardButton("enable", callback_data="enable_help"),
            types.InlineKeyboardButton("disable", callback_data="disable_help"),
            types.InlineKeyboardButton("open", callback_data="open_help")
        )
        kb.row(types.InlineKeyboardButton("close", callback_data="close_help"),
            types.InlineKeyboardButton("openglobal", callback_data="openglobal_help"),
            types.InlineKeyboardButton("closeglobal", callback_data="closeglobal_help")
        )
        kb.row(
            types.InlineKeyboardButton("opengroup", callback_data="opengroup_help"),
            types.InlineKeyboardButton("closegroup", callback_data="closegroup_help"),
            types.InlineKeyboardButton("closeid", callback_data="closeid_help")
        )
        kb.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cmd"))
        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=help_text,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    help_text,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("fstats_help callback edit failed: %s", e)
            bot.answer_callback_query(call.id, "Unable to open fstats_help.", show_alert=False)
        return
        
    # BACK TO CMD
    if data == "back_to_cmd":
        name = call.from_user.first_name if call.from_user else "User"
        user_id = call.from_user.id if call.from_user else call.message.chat.id

        caption = f"""👋 𝐇𝐞𝐲, {name}!
🆔 𝐘𝐨𝐮𝐫 𝐈𝐃: <code>{user_id}</code>
        
<blockquote>»ᴄᴍᴅ ᴄᴏᴍᴍᴀɴᴅ
ᴄᴏᴍᴘʟᴇᴛᴇ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ ɢᴜɪᴅᴇ

<b>ᴡʜᴀᴛ ɪᴛ ᴄᴏɴᴛᴀɪɴꜱ:</b>
• ᴀʟʟ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ ᴄᴀᴛᴇɢᴏʀɪᴢᴇᴅ
• ᴅᴇᴛᴀɪʟᴇᴅ ᴜꜱᴀɴɢᴇ ɪɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ
• ʙᴜᴛᴛᴏɴ-ʙᴀꜱᴇᴅ ɴᴀᴠɪɢᴀᴛɪᴏɴ
• ꜱᴜʙ-ᴄᴀᴛᴇɢᴏʀɪᴇꜱ ꜰᴏʀ ᴇᴀꜱʏ ᴀᴄᴄᴇꜱꜱ

<b>ᴡʜʏ ɪᴛ ᴡᴀꜱ ᴄʀᴇᴀᴛᴇᴅ:</b>
ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴄᴏᴍᴘʟᴇᴛᴇ ᴀɴᴅ ᴀᴅᴍɪɴ-ꜰʀɪᴇɴᴅʟʏ ɢᴜɪᴅᴇ ꜰᴏʀ ᴀʟʟ ʙᴏᴛ ꜰᴇᴀᴛᴜʀᴇꜱ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅꜱ</blockquote>"""

        buttons = [
            [
                types.InlineKeyboardButton("ꜰɪʟᴛᴇʀ", callback_data="ffilter_help"),
                types.InlineKeyboardButton("ᴅᴍꜰɪʟᴛᴇʀ", callback_data="dmffilter_help"),
                types.InlineKeyboardButton("fstatus", callback_data="fstatus_help"),
            ],
            [
                types.InlineKeyboardButton("ꜱᴛᴀᴛꜱ", callback_data="sstats_help"),
                types.InlineKeyboardButton("ʙʀᴏᴀᴅᴄᴀꜱᴛ!!", callback_data="bbroadcast_help"),
                types.InlineKeyboardButton("ᴘɪɴɢ", callback_data="pping_help"),
            ],
            [
                types.InlineKeyboardButton("fstats", callback_data="fstats_help")
            ],
        ]

        try:
            # Try to edit message if it's a photo message
            if call.message.content_type == 'photo':
                bot.edit_message_media(
                    media=types.InputMediaPhoto("https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg"),
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=make_inline_keyboard(buttons)
                )
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption=caption,
                    reply_markup=make_inline_keyboard(buttons),
                    parse_mode="HTML"
                )
            else:
                bot.edit_message_text(
                    caption,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=make_inline_keyboard(buttons),
                    parse_mode="HTML"
                )
            bot.answer_callback_query(call.id)
        except Exception as e:
            logger.exception("back_to_cmd edit failed: %s", e)
            try:
                bot.edit_message_text(
                    caption,
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=make_inline_keyboard(buttons),
                    parse_mode="HTML"
                )
                bot.answer_callback_query(call.id)
            except Exception as e2:
                logger.exception("back_to_cmd: fallback edit_text failed: %s", e2)
                bot.answer_callback_query(call.id, "Unable to go back to cmd.", show_alert=False)
        return                

    # pagination callbacks: page_prev_..., page_next_...
    page_match = re.match(r"^page_(prev|next)_([A-Z0-9]+)_(\d+)$", data)
    if page_match:
        direction, char, current_page = page_match.groups()
        current_page = int(current_page)
        new_page = current_page - 1 if direction == "prev" else current_page + 1
        offset = new_page * 50
        if char == "OTHER":
            regex_filter = {"keyword": {"$regex": "^[^a-zA-Z0-9]"}}
        else:
            regex_filter = {"keyword": {"$regex": f"^{re.escape(char)}", "$options": "i"}}
        
        # UPDATED: Check DM filter settings for #anime keyboard
        settings = get_dm_settings()
        if settings["dm_filters_enabled"]:
            # If /openfilter is ON, combine both normal and DM filters
            normal_filters = list(filters_collection.find(regex_filter).sort("keyword", 1).skip(offset).limit(50))
            dm_filters = list(dm_filters_collection.find(regex_filter).sort("keyword", 1).skip(offset).limit(50))
            filters_list = normal_filters + dm_filters
            filters_list = sorted(filters_list, key=lambda x: x.get("keyword", ""))[:50]
        else:
            # If /closefilter is OFF, show only normal filters
            filters_list = list(filters_collection.find(regex_filter).sort("keyword", 1).skip(offset).limit(50))
            
        if not filters_list:
            bot.answer_callback_query(call.id, "No more filters to show!")
            return
        rows = []
        r = []
        for fdata in filters_list:
            display = short_display(fdata.get("keyword", ""), limit=40)
            btn = types.InlineKeyboardButton(display, callback_data=f"filter_{str(fdata['_id'])}")
            r.append(btn)
            if len(r) == 2:
                rows.append(r)
                r = []
        if r:
            rows.append(r)
        nav = []
        if offset > 0:
            nav.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"page_prev_{char}_{new_page}"))
        if len(filters_list) == 50:
            nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"page_next_{char}_{new_page}"))
        if nav:
            rows.append(nav)
        rows.append([types.InlineKeyboardButton("🔙 Back", callback_data="back_to_letters")])
        try:
            bot.edit_message_text(f"🔍 Filters starting with '{char}' (Page {new_page + 1}):", call.message.chat.id, call.message.message_id, reply_markup=make_inline_keyboard(rows))
            bot.answer_callback_query(call.id)
        except Exception:
            bot.answer_callback_query(call.id, "Unable to update.")
        return

    # back to letters
    if data == "back_to_letters":
        rk = make_reply_keyboard(ANIME_KEYBOARD_LETTERS)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        try:
            bot.send_message(call.from_user.id, "🔍 Select a letter to browse anime filters:", reply_markup=rk)
        except Exception:
            bot.answer_callback_query(call.id, "Unable to open letters.")
        return

    # filter selection: filter_<id or keyword>
    filter_match = re.match(r"^filter_(.+)$", data)
    if filter_match:
        payload = filter_match.group(1)
        fdata = get_filter_by_id(payload)
        if not fdata:
            fdata = get_filter(payload)
        if not fdata:
            bot.answer_callback_query(call.id, "Filter not found!", show_alert=True)
            return
        chat_id = call.message.chat.id
        try:
            if fdata["type"] == "text":
                bot.send_message(chat_id, fdata["data"])
            elif fdata["type"] == "photo":
                bot.send_photo(chat_id, fdata["file_id"], caption=fdata.get("caption", ""))
        except Exception:
            bot.answer_callback_query(call.id, "Failed to send filter.")
        bot.answer_callback_query(call.id)
        return

    # admin filter preview: admin_filter_<id_or_keyword>
    admin_match = re.match(r"^admin_filter_(.+)$", data)
    if admin_match:
        payload = admin_match.group(1)
        fdata = get_filter_by_id(payload)
        if not fdata:
            fdata = get_filter(payload)
        if not fdata:
            bot.answer_callback_query(call.id, "Filter not found!", show_alert=True)
            return
        if fdata["type"] == "text":
            preview = f"📝 Text Filter: {fdata['data'][:200]}..."
        else:
            preview = f"🖼️ Photo Filter\nCaption: {fdata.get('caption','No caption')[:200]}..."
        bot.answer_callback_query(call.id, preview, show_alert=True)
        return

    # show full list callback
    if data == "show_full_list":
        all_filters = get_all_filters()
        all_keys = "\n".join([f"- <code>{f.get('keyword','(no-keyword)')}</code>" for f in all_filters])
        max_chunk = 3800
        try:
            if len(all_keys) > max_chunk:
                for i in range(0, len(all_keys), max_chunk):
                    bot.send_message(call.message.chat.id, all_keys[i:i+max_chunk])
            else:
                bot.send_message(call.message.chat.id, f"📋 <b>All Filters</b>:\n{all_keys}")
        except Exception:
            bot.answer_callback_query(call.id, "Unable to send list.")
        bot.answer_callback_query(call.id)
        return

    # filters pagination (admin)
    filters_page_match = re.match(r"^filters_page_(\d+)$", data)
    if filters_page_match:
        page = int(filters_page_match.group(1))
        all_filters = get_all_filters()
        page_size = 10
        total_pages = (len(all_filters) + page_size - 1) // page_size
        start_idx = page * page_size
        end_idx = start_idx + page_size
        rows = []
        for fdata in all_filters[start_idx:end_idx]:
            display = short_display(fdata.get("keyword",""), limit=50)
            rows.append([types.InlineKeyboardButton(display, callback_data=f"admin_filter_{str(fdata.get('_id'))}")])
        nav = []
        if page > 0:
            nav.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"filters_page_{page - 1}"))
        if end_idx < len(all_filters):
            nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"filters_page_{page + 1}"))
        if nav:
            rows.append(nav)
        rows.append([types.InlineKeyboardButton("📜 Show Full List", callback_data="show_full_list")])
        try:
            bot.edit_message_text(f"📋 Available Filters (Page {page + 1}/{total_pages}):", call.message.chat.id, call.message.message_id, reply_markup=make_inline_keyboard(rows))
            bot.answer_callback_query(call.id)
        except Exception:
            bot.answer_callback_query(call.id, "Unable to paginate.")
        return

    bot.answer_callback_query(call.id, "")

# /filter command - add filter (admin only)
@bot.message_handler(commands=["filter"])
def add_filter(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Sorry, you're not allowed to add filters!\n     🚫 Only <b>Admins</b> and <b>Authorized Users</b> can use this command.")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "❌ Reply to a message to save as filter!")
        return

    parts = message.text.split(None, 1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /filter keyword (reply to message)")
        return
    keyword = parts[1].strip()

    reply_msg = message.reply_to_message
    filter_data = {}
    if reply_msg.content_type == "text":
        filter_data = {"type": "text", "data": reply_msg.text}
    elif reply_msg.content_type == "photo":
        file_id = reply_msg.photo[-1].file_id
        filter_data = {"type": "photo", "file_id": file_id, "caption": reply_msg.caption or ""}
    else:
        bot.reply_to(message, "⚠️ Only text and photo filters are supported!")
        return

    # Check if DM only creation mode is enabled
    settings = get_dm_settings()
    if settings["creation_mode"]:
        save_dm_filter(keyword, filter_data)
        
        # LOG DM FILTER ADDED
        log_message("DM_FILTER_ADDED", f"DM Filter: {keyword}", 
                    message.from_user.id, message.chat.id,
                    message.from_user.username, message.from_user.first_name,
                    message.chat.title if message.chat.title else None,
                    f"Type: {filter_data['type']}")
        
        bot.reply_to(message, f"✅ <b>DM Only Filter</b> saved for: <code>{keyword}</code>")
    else:
        save_filter(keyword, filter_data)
        
        # LOG NORMAL FILTER ADDED
        log_message("FILTER_ADDED", f"Normal Filter: {keyword}", 
                    message.from_user.id, message.chat.id,
                    message.from_user.username, message.from_user.first_name,
                    message.chat.title if message.chat.title else None,
                    f"Type: {filter_data['type']}")
        
        bot.reply_to(message, f"✅ <b>Filter saved for:</b> <code>{keyword}</code>")

# /stop command - delete filter
@bot.message_handler(commands=["stop"])
def stop_filter(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Sorry, you're not allowed to Stop filters!\n🚫 Only <b>Admins</b> and <b>Authorized Users</b> can use this command.")
        return

    parts = message.text.split(None, 1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /stop keyword")
        return
    keyword = parts[1].strip().lower()
    
    # Try to delete from normal filter 
    deleted_normal = delete_filter(keyword)   
    
    if deleted_normal:
        # LOG FILTER DELETED
        log_message("FILTER_DELETED", f"Normal Filter: {keyword}", 
                    message.from_user.id, message.chat.id,
                    message.from_user.username, message.from_user.first_name,
                    message.chat.title if message.chat.title else None)
        
        bot.reply_to(message, f"🗑️ <b>Both Normal Filters</b> removed: <code>{keyword}</code>")
    elif deleted_normal:
        bot.reply_to(message, f"🗑️ <b>Filter removed:</b> <code>{keyword}</code>")
    
    else:
        bot.reply_to(message, f"⚠️ No filter found with keyword: <code>{keyword}</code>")
        
        #bstop dm filter stop check
        
        
# /bstop command - delete dm filter
@bot.message_handler(commands=["bstop"])
def bstop_filter(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "⚠️ Sorry, you're not allowed to Stop filters!\n🚫 Only <b>Admins</b> and <b>Authorized Users</b> can use this command.")
        return

    parts = message.text.split(None, 1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /bstop keyword")
        return
    keyword = parts[1].strip().lower()
    
    # Try to delete from DM filters
    deleted_dm = delete_dm_filter(keyword)
    
    if deleted_dm:
        # LOG DM FILTER DELETED
        log_message("DM_FILTER_DELETED", f"DM Filter: {keyword}", 
                    message.from_user.id, message.chat.id,
                    message.from_user.username, message.from_user.first_name,
                    message.chat.title if message.chat.title else None)
        
        bot.reply_to(message, f"🗑️ <b>DM Filters</b> removed: <code>{keyword}</code>")
   
    elif deleted_dm:
        bot.reply_to(message, f"🗑️ <b>DM Only Filter</b> removed: <code>{keyword}</code>")
    else:
        bot.reply_to(message, f"⚠️ No filter found with keyword: <code>{keyword}</code>")
        
        
# #Anime handler - shows reply keyboard in private or link button in groups
@bot.message_handler(func=lambda m: bool(re.fullmatch(r"#Anime", m.text or "", flags=re.IGNORECASE)))
def anime_keyboard_handler(message: types.Message):
    if message.chat.type == "private":
        rk = make_reply_keyboard(ANIME_KEYBOARD_LETTERS)
        bot.reply_to(message, "🔍 Select a letter to browse anime filters:", reply_markup=rk)
    else:
        ik = types.InlineKeyboardMarkup()
        ik.add(types.InlineKeyboardButton("Click Here", url=f"https://t.me/Roxy_Anime_FilterBot?start=anime_keyboard"))
        bot.reply_to(message, "Please click the button below to browse anime filters in DM:", reply_markup=ik)

# internal helper to open keyboard when /start param anime_keyboard used
def anime_keyboard_handler_private(message: types.Message):
    if message.chat.type == "private":
        rk = make_reply_keyboard(ANIME_KEYBOARD_LETTERS)
        bot.send_message(message.chat.id, "🔍 Select a letter to browse anime filters:", reply_markup=rk)
    else:
        ik = types.InlineKeyboardMarkup()
        ik.add(types.InlineKeyboardButton("Click Here", url=f"https://t.me/Roxy_Anime_FilterBot?start=anime_keyboard"))
        bot.send_message(message.chat.id, "Please click the button below to browse anime filters in DM:", reply_markup=ik)

# Letter selection handler (private) - FIXED FOR DM FILTERS
@bot.message_handler(func=lambda m: (m.chat.type == "private") and bool(re.fullmatch(r"[0-9A-Za-z]|Other", (m.text or ""), flags=re.IGNORECASE)))
def letter_selection_handler(message: types.Message):
    selected_char = (message.text or "").upper().strip()
    update_user_data(message.from_user.id, message.chat.id)
    if selected_char == "OTHER":
        regex_filter = {"keyword": {"$regex": "^[^a-zA-Z0-9]"}}
    else:
        regex_filter = {"keyword": {"$regex": f"^{re.escape(selected_char)}", "$options": "i"}}

    # FIXED: Check DM filter settings for keyboard
    settings = get_dm_settings()
    if settings["dm_filters_enabled"]:
        # If /openfilter is ON, combine both normal and DM filters
        normal_filters = list(filters_collection.find(regex_filter).sort("keyword", 1))
        dm_filters = list(dm_filters_collection.find(regex_filter).sort("keyword", 1))
        filters_list = normal_filters + dm_filters
        filters_list = sorted(filters_list, key=lambda x: x.get("keyword", ""))
    else:
        # If /closefilter is OFF, show only normal filters
        filters_list = list(filters_collection.find(regex_filter).sort("keyword", 1))
    
    if not filters_list:
        bot.reply_to(message, f"No filters found starting with '{selected_char}'", reply_markup=types.ReplyKeyboardRemove())
        return

    rows = []
    row = []
    for fdata in filters_list[:50]:
        display = short_display(fdata.get("keyword",""), limit=40)
        # FIXED: Check if it's DM filter or normal filter and set callback accordingly
        if settings["dm_filters_enabled"] and dm_filters_collection.find_one({"_id": fdata.get('_id')}):
            # DM filter hai - use dmfilter_ prefix
            btn = types.InlineKeyboardButton(display, callback_data=f"dmfilter_{str(fdata['_id'])}")
        else:
            # Normal filter hai - use filter_ prefix  
            btn = types.InlineKeyboardButton(display, callback_data=f"filter_{str(fdata['_id'])}")
        row.append(btn)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    if len(filters_list) > 50:
        rows.append([types.InlineKeyboardButton("⬅️ Previous", callback_data=f"page_prev_{selected_char}_0"),
                     types.InlineKeyboardButton("Next ➡️", callback_data=f"page_next_{selected_char}_0")])

    rows.append([types.InlineKeyboardButton("🔙 Back", callback_data="back_to_letters")])

    try:
        bot.reply_to(message, "⌛ Loading filters...", reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, f"🔍 Filters starting with '{selected_char}':", reply_markup=make_inline_keyboard(rows))
    except Exception:
        logger.exception("letter_selection_handler failed")

# /filters admin command
@bot.message_handler(commands=["filters"])
def list_filters(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "🔒 This command is for admins only to view stats!")
        return

    all_filters = get_all_filters()
    if not all_filters:
        bot.reply_to(message, "📭 No filters found!")
        return

    parts = message.text.split()
    if len(parts) > 1 and parts[1].lower() == "full":
        all_keys = "\n".join([f"- <code>{f.get('keyword','(no-keyword)')}</code>" for f in all_filters])
        max_chunk = 3800
        if len(all_keys) > max_chunk:
            for i in range(0, len(all_keys), max_chunk):
                bot.reply_to(message, all_keys[i:i+max_chunk])
        else:
            bot.reply_to(message, f"📋 <b>Available Filters</b>:\n{all_keys}")
        return

    page_size = 10
    total_pages = (len(all_filters) + page_size - 1) // page_size
    rows = []
    for fdata in all_filters[:page_size]:
        display = short_display(fdata.get("keyword", ""), limit=50)
        rows.append([types.InlineKeyboardButton(display, callback_data=f"admin_filter_{str(fdata.get('_id'))}")])
    if total_pages > 1:
        rows.append([types.InlineKeyboardButton("Next ➡️", callback_data="filters_page_1")])
    rows.append([types.InlineKeyboardButton("📜 Show Full List", callback_data="show_full_list")])
    bot.reply_to(message, f"📋 Available Filters (Page 1/{total_pages}):", reply_markup=make_inline_keyboard(rows))

# /ping
# /ping
@bot.message_handler(commands=["ping"])
def ping_command(message: types.Message):
    # LOG COMMAND USAGE
    log_message("COMMAND_USED", f"/ping - Bot status checked", 
                message.from_user.id, message.chat.id,
                message.from_user.username if message.from_user else None,
                message.from_user.first_name if message.from_user else None,
                message.chat.title if message.chat.title else None)
    
    try:
        # Calculate ping
        start_time = time.time()
        temp_msg = bot.send_message(message.chat.id, "🏓 Calculating ping...")
        end_time = time.time()
        ping_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Delete the temporary message
        bot.delete_message(message.chat.id, temp_msg.message_id)
        
        # Get system stats using psutil
        ram_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=0.1)
        disk_usage = psutil.disk_usage('/').percent
        
        # Format the response
        caption = f"""🏓 ᴩᴏɴɢ : {ping_time:.3f}ᴍs

˹📝 sʏsᴛᴇᴍ sᴛᴀᴛs :

✨ ᴜᴩᴛɪᴍᴇ : {get_bot_uptime()}
❄ ʀᴀᴍ : {ram_usage:.1f}%
💫 ᴄᴩᴜ : {cpu_usage:.1f}%
🔮 ᴅɪsᴋ : {disk_usage:.1f}%"""
        
        # Create inline keyboard with "Add to Group" button using row method
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("➕ Add Me To Your Group", url="https://t.me/Roxy_Anime_FilterBot?startgroup=true")
        )
        
        # You can add more rows if needed:
        # keyboard.row(
        #     types.InlineKeyboardButton("🔙 Back", callback_data="back_to_start"),
        #     types.InlineKeyboardButton("📊 Stats", callback_data="show_stats")
        # )
        
        # Send photo with caption and button
        bot.send_photo(
            chat_id=message.chat.id,
            photo="https://graph.org/file/b64391fde1b12e62b2157-0fa3f3eb118b6c5d71.jpg",
            caption=caption,
            reply_markup=keyboard,
            reply_to_message_id=message.message_id,
            parse_mode="HTML"
        )
        
    except Exception as e:
        bot.reply_to(message, f"🏓 ᴩᴏɴɢ!\n\nError: {str(e)}")

# /stats command
@bot.message_handler(commands=["stats"])
def stats_handler(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "🔒 This command is for admins only to view stats!")
        return
    
    # LOG ADMIN COMMAND
    log_message("ADMIN_COMMAND", f"/stats - Bot statistics checked", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None)
    
    user_count = get_user_count()
    group_count = get_group_count()
    
    stats_msg = f"""<blockquote>📊 <b>Bot Statistics</b>

👤 <b>Users:</b> <code>{user_count}</code>
👥 <b>Groups:</b> <code>{group_count}</code>
🧠 <b>Total Filters:</b> <code>{filters_collection.count_documents({})}</code>
🔧 <b>DM Only Filters:</b> <code>{dm_filters_collection.count_documents({})}</code>

👮 <b>Admins:</b>
"""
    for admin_id in [ADMIN_ID] + OTHER_ADMINS:
        stats_msg += f"- <code>{admin_id}</code>\n"
    stats_msg += "\n🟢 <b>Bot Status:</b> Active</blockquote>"
    bot.reply_to(message, stats_msg)

# /bc broadcast (admin only)
@bot.message_handler(commands=["broadcast"])
def broadcast_handler(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "🔒 This command is for admins only to broadcast!")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Please reply to a message with /broadcast")
        return

    total_users = get_user_count()
    total_groups = get_group_count()
    total = total_users + total_groups

    progress_msg = bot.reply_to(message, f"📡 <b>Broadcast Started</b>\n\n👤 Users: <code>{total_users}</code>\n👥 Groups: <code>{total_groups}</code>\n\n⏳ Sending to {total} chats...")
    success = 0
    failed_users = 0
    failed_groups = 0

    for user in users_collection.find({"bot_token": bot.token}):
        try:
            ok = send_copy_to_chat(int(user["user_id"]), message.reply_to_message)
            if ok:
                success += 1
            else:
                failed_users += 1
        except Exception:
            failed_users += 1
        time.sleep(0.1)

    for group in groups_collection.find({"bot_token": bot.token}):
        try:
            ok = send_copy_to_chat(int(group["chat_id"]), message.reply_to_message)
            if ok:
                success += 1
            else:
                failed_groups += 1
        except Exception:
            failed_groups += 1
        time.sleep(0.1)

    result_msg = (
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"📊 Total: <code>{total}</code>\n"
        f"✔️ Success: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed_users + failed_groups}</code>\n\n"
        f"Failed users: <code>{failed_users}</code>\n"
        f"Failed groups: <code>{failed_groups}</code>"
    )
    
    # LOG BROADCAST
    log_message("ADMIN_COMMAND", f"/broadcast - Sent to {total} chats", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None,
                f"Success: {success}, Failed: {failed_users + failed_groups}")
    
    try:
        bot.edit_message_text(result_msg, progress_msg.chat.id, progress_msg.message_id)
    except Exception:
        bot.reply_to(message, result_msg)
        
# abroadcast to admin
# /abroadcast - Broadcast only to admins (DM only)
@bot.message_handler(commands=["abroadcast"])
def admin_broadcast_handler(message: types.Message):
    sender = message.from_user.id if message.from_user else None
    if sender not in [ADMIN_ID] + OTHER_ADMINS:
        bot.reply_to(message, "🔒 This command is for admins only!")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Please reply to a message with /abroadcast")
        return

    # Get all admins list
    all_admins = [ADMIN_ID] + OTHER_ADMINS
    total_admins = len(all_admins)

    progress_msg = bot.reply_to(message, f"📡 <b>Admin Broadcast Started</b>\n\n👮 Admins: <code>{total_admins}</code>\n\n⏳ Sending to {total_admins} admins...")
    success = 0
    failed = 0

    # Broadcast only to admins (DM only)
    for admin_id in all_admins:
        try:
            ok = send_copy_to_chat(int(admin_id), message.reply_to_message)
            if ok:
                success += 1
            else:
                failed += 1
        except Exception:
            failed += 1
        time.sleep(0.1)

    result_msg = (
        f"✅ <b>Admin Broadcast Completed!</b>\n\n"
        f"📊 Total Admins: <code>{total_admins}</code>\n"
        f"✔️ Success: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed}</code>"
    )
    
    # LOG ADMIN BROADCAST
    log_message("ADMIN_COMMAND", f"/abroadcast - Sent to {total_admins} admins", 
                message.from_user.id, message.chat.id,
                message.from_user.username, message.from_user.first_name,
                message.chat.title if message.chat.title else None,
                f"Success: {success}, Failed: {failed}")
    
    try:
        bot.edit_message_text(result_msg, progress_msg.chat.id, progress_msg.message_id)
    except Exception:
        bot.reply_to(message, result_msg)


                
# Reply on exact keyword (group or private)
@bot.message_handler(func=lambda m: (m.content_type == "text") and (m.chat.type in ("private","group","supergroup")))
def filter_responder(message: types.Message):
    try:
        # BUG FIX: Only update groups, NOT users (unless it's private chat)
        if message.chat.type != "private":
            # Only update groups collection
            groups_collection.update_one(
                {"chat_id": message.chat.id, "bot_token": bot.token},
                {"$set": {"chat_id": message.chat.id, "bot_token": bot.token}},
                upsert=True
            )
        else:
            # Private chat mein dono update karo
            update_user_data(message.from_user.id, message.chat.id)
    except Exception:
        pass

    text = (message.text or "").lower().strip()
    
    # Check DM only filters first (if enabled)
    settings = get_dm_settings()
    if settings["dm_filters_enabled"]:
        if message.chat.type == "private" or is_dm_filter_enabled_for_group(message.chat.id):
            dm_fdata = get_dm_filter(text)
            if dm_fdata:
                try:
                    # LOG FILTER USAGE
                    log_message("FILTER_USED", f"DM Filter: {text}", 
                              message.from_user.id if message.from_user else None,
                              message.chat.id,
                              message.from_user.username if message.from_user else None,
                              message.from_user.first_name if message.from_user else None,
                              message.chat.title if message.chat.title else None,
                              f"Type: {dm_fdata['type']}")
                    
                    if dm_fdata["type"] == "text":
                        bot.reply_to(message, dm_fdata["data"])
                    elif dm_fdata["type"] == "photo":
                        bot.send_photo(message.chat.id, dm_fdata["file_id"], caption=dm_fdata.get("caption",""))
                    return
                except Exception:
                    logger.exception("DM filter_responder send failed")
                    return
    
    # Original normal filters logic
    fdata = get_filter(text)
    if fdata:
        try:
            # LOG FILTER USAGE
            log_message("FILTER_USED", f"Normal Filter: {text}", 
                      message.from_user.id if message.from_user else None,
                      message.chat.id,
                      message.from_user.username if message.from_user else None,
                      message.from_user.first_name if message.from_user else None,
                      message.chat.title if message.chat.title else None,
                      f"Type: {fdata['type']}")
            
            if fdata["type"] == "text":
                bot.reply_to(message, fdata["data"])
            elif fdata["type"] == "photo":
                bot.send_photo(message.chat.id, fdata["file_id"], caption=fdata.get("caption",""))
            return
        except Exception:
            logger.exception("filter_responder send failed")
            return
    
    all_filters = list(filters_collection.find({}))
    for filter_data in all_filters:
        keyword = filter_data.get("keyword", "").lower()
        if keyword:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                try:
                    # LOG FILTER USAGE (pattern match)
                    log_message("FILTER_USED", f"Pattern Match: {text} -> {keyword}", 
                              message.from_user.id if message.from_user else None,
                              message.chat.id,
                              message.from_user.username if message.from_user else None,
                              message.from_user.first_name if message.from_user else None,
                              message.chat.title if message.chat.title else None,
                              f"Type: {filter_data['type']}")
                    
                    if filter_data["type"] == "text":
                        bot.reply_to(message, filter_data["data"])
                    elif filter_data["type"] == "photo":
                        bot.send_photo(message.chat.id, filter_data["file_id"], caption=filter_data.get("caption",""))
                    break
                except Exception:
                    logger.exception("filter_responder send failed")
                    break

# Start polling
if __name__ == "__main__":
    print("🤖 Bot (TeleBot) is running with DM Filters System and Logs...")
    bot.infinity_polling(timeout=60, long_polling_timeout=5)
