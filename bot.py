def save_st(key, value):import telebot
from telebot import types
import sqlite3
import json
import math
import requests

# --- CONFIG ---
TOKEN = '8110611204:AAHxWhj0WkfdhRZK4t6mLfYxbzRNwkbMKHY'
API_KEY = "APISCVZWF17742506741000" # သင့် Key ထည့်ပြီးသားပါ
ADMIN_ID = 5555392546
DB_NAME = 'juvira_shop.db'

bot = telebot.TeleBot(TOKEN)

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    conn.commit(); conn.close()

init_db()

def get_st(key):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key=?', (key,))
    row = c.fetchone(); conn.close()
    return json.loads(row[0]) if row and key == "prices" else (row[0] if row else None)
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    val = json.dumps(value) if key == "prices" else str(value)
    c.execute('INSERT OR REPLACE INTO settings VALUES (?, ?)', (key, val))
    conn.commit(); conn.close()

# --- JUVIRA API CORE ---
def sync_prices_from_api():
    """API မှ ဈေးနှုန်းများကို ဆွဲယူပြီး အလိုအလျောက် သိမ်းဆည်းခြင်း"""
    url = "https://api.juvirastore.com/services"
    # ပုံထဲကအတိုင်း Body ထဲမှာ api_key တစ်ခုတည်း ပို့ရုံပါပဲ
    payload = {"api_key": API_KEY}
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        res_data = response.json()
        
        if res_data.get("status") == True:
            services = res_data.get("data")
            new_prices = {}
            # အမြတ် ၅% ပေါင်းမည်
            profit = 1.05 
            
            for s in services:
                cat = s['kategori']
                # ရောင်းအကောင်းဆုံးဂိမ်းများသာ ရွေးမည်
                if cat in ["Mobile Legends", "Free Fire", "PUBG Mobile"]:
                    name = s['nama_layanan']
                    p_id = s['id']
                    # Gold Price ပေါ်အခြေခံတွက်ချက်မည်
                    cost = float(s.get('harga_gold', s['harga']))
                    sell_price = int(math.ceil((cost * profit) / 50.0)) * 50
                    
                    if cat not in new_prices: new_prices[cat] = []
                    new_prices[cat].append((name, sell_price, p_id))
            
            save_st("prices", new_prices)
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    if uid == ADMIN_ID:
        mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
        mk.add("🔄 ဈေးနှုန်း Auto Update လုပ်မည်", "💰 လက်ကျန်ငွေစစ်မည်")
        bot.send_message(m.chat.id, "🛠 Admin Panel (Juvirastore Active)", reply_markup=mk)
    else:
        mk = types.ReplyKeyboardMarkup(resize_keyboard=True); mk.add("🛒 ဈေးဝယ်ရန်")
        bot.send_message(m.chat.id, "🌟 GOLD STAR GAME SHOP မှ ကြိုဆိုပါတယ်", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text == "🔄 ဈေးနှုန်း Auto Update လုပ်မည်" and m.from_user.id == ADMIN_ID)
def admin_sync(m):
    bot.send_message(m.chat.id, "⏳ API မှ ဈေးနှုန်းများ ရယူနေပါသည်...")
    if sync_prices_from_api():
        bot.send_message(m.chat.id, "✅ ဈေးနှုန်းများ အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။")
    else:
        bot.send_message(m.chat.id, "❌ Error! API ချိတ်ဆက်မှု မအောင်မြင်ပါ။ IP Whitelist လုပ်ထားခြင်း ရှိမရှိ စစ်ဆေးပါ။")

@bot.message_handler(func=lambda m: m.text == "🛒 ဈေးဝယ်ရန်")
def user_shop(m):
    prices = get_st("prices")
    if not prices:
        return bot.send_message(m.chat.id, "လက်ရှိ ရောင်းချပေးနိုင်သော ပစ္စည်းမရှိသေးပါ။ Admin ကို အကြောင်းကြားပေးပါ။")
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for g in prices.keys(): mk.add(g)
    bot.send_message(m.chat.id, "🎮 ဝယ်ယူမည့်ဂိမ်းကို ရွေးချယ်ပါ-", reply_markup=mk)

# Bot အား စတင်ပတ်မောင်းခြင်း
print("Bot is starting...")
bot.infinity_polling()
