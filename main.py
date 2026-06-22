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
    return "R.downloader bot is running professionally!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- TELEGRAM BOT SETUP ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing!")

bot = telebot.TeleBot(BOT_TOKEN)

# Temporary user storage for states and search tracking
user_states = {}
search_cache = {}

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
    """Super Professional Welcome Message for R.downloader bot"""
    welcome_text = (
        f"🤖 *Welcome to R.downloader bot, {message.from_user.first_name}!*\n\n"
        "⚡ _Your premium, ultra-fast solution for extracting direct streaming and high-speed download links seamlessly._\n\n"
        "🔥 *Core Features:* \n"
        "• Direct Extraction via Video/Audio Links\n"
        "• Smart Platform Search (YouTube & General Web)\n"
        "• Zero buffering, instant media details with posters\n\n"
        "🎯 *How to Start:* \n"
        "💡 Simply *paste any video link* directly to fetch its details, or click the button below to *search by keywords/titles*."
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
        InlineKeyboardButton("🌐 General Web", callback_data="plat_ytsearch")
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
    platform_prefix = call.data.split("_")[1]
    user_states[call.message.chat.id] = platform_prefix
    
    bot.send_message(
        call.message.chat.id,
        "🔍 *Great! Now type your search keyword/title:*",
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("selectvideo_"))
def handle_video_selection(call):
    """Triggered when a user clicks a number button from the top 10 search results"""
    chat_id = call.message.chat.id
    _, cache_key, index = call.data.split("_")
    
    # Retrieve the actual URL from cache
    lookup_key = f"{cache_key}_{index}"
    video_url = search_cache.get(lookup_key)
    
    if not video_url:
        bot.send_message(chat_id, "❌ *Session expired! Please search again.*", parse_mode="Markdown")
        return
        
    msg = bot.send_message(chat_id, "⚡ *Extracting poster and high-speed links, please wait...*", parse_mode="Markdown")
    info = extract_video_info(video_url, is_search=False)
    
    if not info:
        bot.edit_message_text("❌ *Failed to extract link info.*", chat_id, msg.message_id, parse_mode="Markdown")
        return
        
    title = info.get('title', 'No Title')
    poster = info.get('thumbnail', '')
    duration = format_duration(info.get('duration'))
    stream_url = info.get('url', '')

    response_text = (
        f"🎬 *Title:* {title}\n"
        f"⏱️ *Duration:* {duration}\n\n"
        f"📥 *Download / Play Link:* \n[⚡ Click Here to Watch or Download]({stream_url})"
    )
    
    bot.delete_message(chat_id, msg.message_id)
    if poster:
        bot.send_photo(chat_id, poster, caption=response_text, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, response_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    # Case 1: Direct link search
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
            f"📥 *Download / Play Link:* \n[⚡ Click Here to Watch or Download]({stream_url})"
        )
        
        bot.delete_message(chat_id, msg.message_id)
        if poster:
            bot.send_photo(chat_id, poster, caption=response_text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, response_text, parse_mode="Markdown")

    # Case 2: Keyword Title Search
    elif chat_id in user_states:
        platform = user_states[chat_id]
        search_query = f"{platform}10:{text}"
        
        msg = bot.send_message(chat_id, f"🔍 *Searching Top 10 results for:* `{text}`...", parse_mode="Markdown")
        search_results = extract_video_info(search_query, is_search=True)
        
        if not search_results or 'entries' not in search_results:
            bot.edit_message_text("❌ *No results found or platform error.*", chat_id, msg.message_id, parse_mode="Markdown")
            return
            
        entries = list(search_results['entries'])[:10]
        
        list_text = f"🎯 *Top 10 Results for* `{text}`:\n\n"
        markup = InlineKeyboardMarkup()
        
        # Create unique cache key based on user chat_id to store URLs safely without 64-byte limit error
        cache_key = str(chat_id)
        
        row_buttons = []
        for idx, entry in enumerate(entries, start=1):
            title = entry.get('title', f'Video {idx}')
            video_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
            
            # Save to temporary backend cache
            search_cache[f"{cache_key}_{idx}"] = video_url
            
            list_text += f"{idx}. *{title}*\n"
            
            # Generate inline numerical selector buttons [1], [2], [3]...
            btn = InlineKeyboardButton(f"[{idx}]", callback_data=f"selectvideo_{cache_key}_{idx}")
            row_buttons.append(btn)
            
            # Group buttons into rows of 5 for ultimate clean layout
            if len(row_buttons) == 5 or idx == len(entries):
                markup.row(*row_buttons)
                row_buttons = []

        list_text += "\n👇 *Click on the number button below to fetch its Poster & Download Link!*"
        
        bot.delete_message(chat_id, msg.message_id)
        bot.send_message(chat_id, list_text, parse_mode="Markdown", reply_markup=markup)
        
        # Clear searching state
        del user_states[chat_id]
    else:
        bot.send_message(
            chat_id, 
            "💡 *Please paste a valid video URL, or click 'Search Content' from /start to look up keywords!*", 
            parse_mode="Markdown"
        )

# --- START BOT & SERVER ---
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("R.downloader bot is successfully polling...")
    bot.infinity_polling()
