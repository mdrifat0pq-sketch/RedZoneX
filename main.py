import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- FLASK SERVER FOR RENDER UPTIME ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running professionally!"

def run_web_server():
    # Render automatically provides a PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- TELEGRAM BOT SETUP ---
# Fetch Token from Render Environment Variables for security
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# Temporary user state storage for platform selection
user_states = {}

# --- HELPER FUNCTIONS ---
def format_duration(seconds):
    """Converts seconds into HH:MM:SS or MM:SS format"""
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def extract_video_info(url_or_search, is_search=False):
    """Extracts metadata using yt-dlp without downloading"""
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist' if is_search else False,
        'skip_download': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url_or_search, download=False)
            return info
        except Exception as e:
            print(f"Error extracting data: {e}")
            return None

# --- BOT COMMANDS & HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Professional Welcome Message with Rich Text and Interface"""
    welcome_text = (
        f"👋 *Welcome to the Ultimate Media Streamer Bot, {message.from_user.first_name}!*\n\n"
        "⚡ *What can I do for you?*\n"
        "• Extract high-speed streaming & download links.\n"
        "• Search videos directly across multiple platforms.\n"
        "• Support for YouTube, Facebook, and many more.\n\n"
        "🎯 *How to use:* \n"
        "1️⃣ Simply paste any video link directly to get immediate details.\n"
        "2️⃣ Or, click the button below to search for keywords."
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔍 Search Content", callback_data="select_platform"))
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="Markdown", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "select_platform")
def choose_platform(call):
    """Platform Selection Menu"""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📺 YouTube", callback_data="plat_ytsearch"),
        InlineKeyboardButton("🌐 General Web", callback_data="plat_ytsearch") # yt-dlp uses ytsearch for general queries too
    )
    
    bot.edit_message_text(
        "🎯 *Select your preferred platform to search:*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("plat_"))
def platform_selected(call):
    platform_prefix = call.data.split("_")[1] # e.g., ytsearch
    user_states[call.message.chat.id] = platform_prefix
    
    bot.send_message(
        call.message.chat.id,
        "🔍 *Great! Now type your search keyword/title:*",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Check if input is a direct link
    if text.startswith("http://") or text.startswith("https://"):
        msg = bot.send_message(chat_id, "⚡ *Processing link, please wait...*", parse_mode="Markdown")
        info = extract_video_info(text, is_search=False)
        
        if not info:
            bot.edit_message_text("❌ *Failed to extract link info. Make sure the link is valid.*", chat_id, msg.message_id, parse_mode="Markdown")
            return
            
        title = info.get('title', 'No Title')
        poster = info.get('thumbnail', '')
        duration = format_duration(info.get('duration'))
        stream_url = info.get('url', '')

        response_text = (
            f"🎬 *Title:* {title}\n"
            f"⏱️ *Duration:* {duration}\n\n"
            f"🔗 *Direct Link:* [Click to Play/Download]({stream_url})"
        )
        
        bot.delete_message(chat_id, msg.message_id)
        if poster:
            bot.send_photo(chat_id, poster, caption=response_text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, response_text, parse_mode="Markdown", disable_web_page_preview=False)

    # Else treating it as search query if platform is selected
    elif chat_id in user_states:
        platform = user_states[chat_id]
        search_query = f"{platform}10:{text}" # yt-dlp syntax for top 10 results
        
        msg = bot.send_message(chat_id, f"🔍 *Searching for Top 10 results for:* `{text}`...", parse_mode="Markdown")
        search_results = extract_video_info(search_query, is_search=True)
        
        if not search_results or 'entries' not in search_results:
            bot.edit_message_text("❌ *No results found or platform error.*", chat_id, msg.message_id, parse_mode="Markdown")
            return
            
        entries = list(search_results['entries'])[:10]
        
        markup = InlineKeyboardMarkup()
        for idx, entry in enumerate(entries, start=1):
            # yt-dlp flat extract gives id/url or title
            title = entry.get('title', f'Video {idx}')
            video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
            markup.add(InlineKeyboardButton(f"🎬 {idx}. {title[:30]}...", callback_data=f"sel_{video_url[:40]}")) 
            # Note: Callback data has a 64-byte limit. For production, storing URLs in a dict/DB is recommended.
            # As a shortcut, we store the actual full text in the state to retrieve on click.
            user_states[f"url_{chat_id}_{idx}"] = video_url

        # Let's present a cleaner list via text and custom inline trigger
        list_text = f"🎯 *Top 10 Results for* `{text}`:\n\n"
        for idx, entry in enumerate(entries, start=1):
            list_text += f"{idx}. *{entry.get('title')}*\n"
            
        list_text += "\n👇 *Click on the links below or paste the specific link to fetch media details!*"
        
        bot.delete_message(chat_id, msg.message_id)
        
        # To bypass callback 64 byte limit safely, we print them out with numbers
        bot.send_message(chat_id, list_text, parse_mode="Markdown")
        # Clear state after search to prevent loop
        del user_states[chat_id]
    else:
        bot.send_message(
            chat_id, 
            "💡 *Please paste a valid video URL, or click 'Search Content' from /start command!*", 
            parse_mode="Markdown"
        )

# --- START BOT & SERVER ---
if __name__ == "__main__":
    # Start Web Server in background thread for Render
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Bot is successfully pooling...")
    bot.infinity_polling()
