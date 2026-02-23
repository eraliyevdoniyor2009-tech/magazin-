#manbaa 
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import sqlite3
from datetime import datetime
import json
import random
import string
import asyncio
#manbaa 
# Bot configuration
API_TOKEN = '8162367529:AAH4QsdiIgObGGDiszQRywfLF4Vk94aJIcE'
ADMIN_ID = 8347167027

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Database setup
def init_db():
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        phone TEXT,
        full_name TEXT,
        referrer_id INTEGER,
        balance INTEGER DEFAULT 0,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_blocked INTEGER DEFAULT 0,
        language TEXT DEFAULT 'uz'
    )''')
    
    # Admins table
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Categories table
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        old_price REAL,
        category_id INTEGER,
        image_id TEXT,
        sizes TEXT,
        stock INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        views INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )''')
    
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE,
        user_id INTEGER,
        items TEXT,
        total_price REAL,
        status TEXT DEFAULT 'pending',
        payment_check TEXT,
        delivery_address TEXT,
        delivery_method TEXT,
        payment_method TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')
    
    # Cart table
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        size TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    # Wishlist table
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (product_id) REFERENCES products (id),
        UNIQUE(user_id, product_id)
    )''')
    
    # Reviews table
    c.execute('''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        order_id INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    # Channels table
    c.execute('''CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT UNIQUE,
        channel_username TEXT,
        channel_name TEXT,
        is_active INTEGER DEFAULT 1,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # Promocodes table
    c.execute('''CREATE TABLE IF NOT EXISTS promocodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        discount_percent INTEGER,
        discount_amount REAL,
        max_uses INTEGER,
        used_count INTEGER DEFAULT 0,
        valid_from TIMESTAMP,
        valid_until TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # User promocode usage table
    c.execute('''CREATE TABLE IF NOT EXISTS user_promocodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        promocode_id INTEGER,
        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (promocode_id) REFERENCES promocodes (id)
    )''')
    
    # Notifications table
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )''')
    
    # Insert default admin
    c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
    
    # Default settings
    default_settings = [
        ('card_number', '8600 1234 5678 9012'),
        ('card_owner', 'SHOP OWNER'),
        ('referral_bonus', '5000'),
        ('referral_gift_points', '50000'),
        ('min_order_amount', '50000'),
        ('delivery_price', '25000'),
        ('free_delivery_from', '200000'),
        ('shop_phone', '+998900113836'),
        ('shop_email', 'support@shop.uz'),
        ('shop_address', 'Toshkent, O\'zbekiston'),
        ('work_hours', '9:00 - 20:00'),
        ('currency', 'so\'m')
    ]
    
    for key, value in default_settings:
        c.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()

init_db()

# FSM States
class Registration(StatesGroup):
    phone = State()
    full_name = State()

class AddCategory(StatesGroup):
    name = State()
    description = State()

class AddProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    old_price = State()
    sizes = State()
    stock = State()
    image = State()

class EditProduct(StatesGroup):
    product_id = State()
    field = State()
    value = State()

class SendBroadcast(StatesGroup):
    message = State()
    confirm = State()

class AddChannel(StatesGroup):
    channel_id = State()

class OrderCheckout(StatesGroup):
    delivery_method = State()
    delivery_address = State()
    payment_method = State()
    notes = State()
    payment_check = State()
    promocode = State()

class ChatWithUser(StatesGroup):
    user_id = State()
    message = State()

class AddPromocode(StatesGroup):
    code = State()
    discount_type = State()
    discount_value = State()
    max_uses = State()
    valid_days = State()

class LeaveReview(StatesGroup):
    product_id = State()
    rating = State()
    comment = State()

class EditSettings(StatesGroup):
    key = State()
    value = State()

# Helper functions
def is_admin(user_id):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT * FROM admins WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None or user_id == ADMIN_ID

def is_user_registered(user_id):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def is_user_blocked(user_id):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT is_blocked FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

async def check_subscription(user_id):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT channel_id FROM channels WHERE is_active = 1')
    channels = c.fetchall()
    conn.close()
    
    if not channels:
        return True
    
    for (channel_id,) in channels:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logging.error(f"Error checking subscription: {e}")
            continue
    
    return True
#manbbaa @krv_coder
def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_setting(key, default=''):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else default

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("🛍 Mahsulotlar"), KeyboardButton("🛒 Savat"))
    keyboard.add(KeyboardButton("📦 Buyurtmalarim"), KeyboardButton("❤️ Sevimlilar"))
    keyboard.add(KeyboardButton("💎 Referal"), KeyboardButton("📊 Statistika"))
    keyboard.add(KeyboardButton("ℹ️ Ma'lumot"), KeyboardButton("☎️ Bog'lanish"))
    return keyboard

def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("📊 Statistika"), KeyboardButton("📢 Reklama"))
    keyboard.add(KeyboardButton("📁 Kategoriyalar"), KeyboardButton("📦 Mahsulotlar"))
    keyboard.add(KeyboardButton("🛍 Buyurtmalar"), KeyboardButton("👥 Foydalanuvchilar"))
    keyboard.add(KeyboardButton("🎁 Promokodlar"), KeyboardButton("⭐ Sharhlar"))
    keyboard.add(KeyboardButton("⚙️ Sozlamalar"), KeyboardButton("🔙 Orqaga"))
    return keyboard

def format_price(price):
    """Format price with thousand separators"""
    return f"{price:,.0f}".replace(',', ' ')

# Middleware for blocking users
async def check_user_blocked(user_id):
    if is_user_blocked(user_id):
        return True
    return False

# Start command
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    
    # Check if blocked
    if await check_user_blocked(user_id):
        await message.answer("❌ Sizning akkauntingiz bloklangan. Qo'shimcha ma'lumot uchun administratorga murojaat qiling.")
        return
    
    # Check subscription
    if not await check_subscription(user_id):
        conn = sqlite3.connect('shop.db')
        c = conn.cursor()
        c.execute('SELECT channel_username, channel_name FROM channels WHERE is_active = 1')
        channels = c.fetchall()
        conn.close()
        
        markup = InlineKeyboardMarkup(row_width=1)
        for username, name in channels:
            markup.add(InlineKeyboardButton(f"✅ {name}", url=f"https://t.me/{username}"))
        markup.add(InlineKeyboardButton("♻️ Tekshirish", callback_data="check_subscription"))
        
        await message.answer(
            "🔒 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak:</b>",
            reply_markup=markup,
            parse_mode='HTML'
        )
        return
    
    # Check if user is registered
    if not is_user_registered(user_id):
        # Check for referral
        args = message.get_args()
        if args and args.startswith('ref'):
            referrer_id = args[3:]
            await state.update_data(referrer_id=referrer_id)
        
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
        
        await message.answer(
            f"👋 <b>Xush kelibsiz, {message.from_user.first_name}!</b>\n\n"
            "🛍 Online do'konimizga xush kelibsiz!\n\n"
            "📱 Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        await Registration.phone.set()
    else:
        # Admin check
        if is_admin(user_id):
            await message.answer(
                "👨‍💼 <b>Admin panel</b>\n\n"
                "Kerakli bo'limni tanlang:",
                reply_markup=get_admin_keyboard(),
                parse_mode='HTML'
            )
        else:
            conn = sqlite3.connect('shop.db')
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM cart WHERE user_id = ?', (user_id,))
            cart_count = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM wishlist WHERE user_id = ?', (user_id,))
            wishlist_count = c.fetchone()[0]
            conn.close()
            
            await message.answer(
                f"👋 <b>Xush kelibsiz, {message.from_user.first_name}!</b>\n\n"
                f"🛒 Savat: {cart_count} ta mahsulot\n"
                f"❤️ Sevimlilar: {wishlist_count} ta mahsulot\n\n"
                "🛍 Mahsulotlarni ko'rish uchun tugmani bosing:",
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )

# Check subscription callback
@dp.callback_query_handler(lambda c: c.data == 'check_subscription', state='*')
async def check_sub_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    if await check_subscription(user_id):
        await callback.message.delete()
        await callback.message.answer(
            "✅ <b>A'zolik tasdiqlandi!</b>\n\n"
            "Endi botdan foydalanishingiz mumkin.",
            parse_mode='HTML'
        )
        await cmd_start(callback.message, state)
    else:
        await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)

# Registration handlers
@dp.message_handler(content_types=['contact'], state=Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    
    await message.answer(
        "✅ Telefon raqam qabul qilindi!\n\n"
        "👤 Endi to'liq ismingizni kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await Registration.full_name.set()

@dp.message_handler(state=Registration.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text
    data = await state.get_data()
    phone = data.get('phone')
    referrer_id = data.get('referrer_id')
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    # Insert user
    c.execute('''INSERT INTO users (user_id, username, phone, full_name, referrer_id) 
                 VALUES (?, ?, ?, ?, ?)''',
              (message.from_user.id, message.from_user.username, phone, full_name, referrer_id))
    
    # Add referral bonus
    if referrer_id:
        bonus = int(get_setting('referral_bonus', '5000'))
        c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (bonus, referrer_id))
        
        # Add notification
        c.execute('''INSERT INTO notifications (user_id, title, message)
                     VALUES (?, ?, ?)''',
                  (referrer_id, "🎉 Yangi referal!",
                   f"👤 {full_name} sizning havolangiz orqali ro'yxatdan o'tdi.\n💰 +{format_price(bonus)} {get_setting('currency')} bonus qo'shildi!"))
        
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 <b>Yangi referal!</b>\n\n"
                f"👤 {full_name} sizning havolangiz orqali ro'yxatdan o'tdi.\n"
                f"💰 +{format_price(bonus)} {get_setting('currency')} bonus qo'shildi!",
                parse_mode='HTML'
            )
        except:
            pass
    
    conn.commit()
    conn.close()
    
    await state.finish()
    
    await message.answer(
        f"✅ <b>Ro'yxatdan o'tish muvaffaqiyatli!</b>\n\n"
        f"👤 Ism: {full_name}\n"
        f"📱 Telefon: {phone}\n\n"
        "🛍 Xarid qilishni boshlashingiz mumkin!",
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )

# Main menu handlers
@dp.message_handler(lambda m: m.text == "🛍 Mahsulotlar")
async def show_products(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await cmd_start(message, None)
        return
    
    if await check_user_blocked(message.from_user.id):
        await message.answer("❌ Sizning akkauntingiz bloklangan.")
        return
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT id, name, description FROM categories WHERE is_active = 1 ORDER BY name')
    categories = c.fetchall()
    conn.close()
    
    if not categories:
        await message.answer("❌ Hozircha kategoriyalar yo'q")
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    for cat_id, name, desc in categories:
        markup.insert(InlineKeyboardButton(f"📁 {name}", callback_data=f"cat_{cat_id}"))
    
    markup.row(InlineKeyboardButton("🔍 Qidiruv", switch_inline_query_current_chat=""))
    
    await message.answer(
        "📁 <b>Kategoriyalar:</b>\n\n"
        "Kerakli kategoriyani tanlang yoki qidiruv tugmasini bosing:",
        reply_markup=markup,
        parse_mode='HTML'
    )

# Category callback
@dp.callback_query_handler(lambda c: c.data.startswith('cat_'))
async def show_category_products(callback: types.CallbackQuery):
    cat_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT name FROM categories WHERE id = ?', (cat_id,))
    cat_name = c.fetchone()
    
    c.execute('''SELECT id, name, price, old_price, stock 
                 FROM products 
                 WHERE category_id = ? AND is_active = 1 
                 ORDER BY name''', (cat_id,))
    products = c.fetchall()
    conn.close()
    
    if not products:
        await callback.answer("❌ Bu kategoriyada mahsulotlar yo'q")
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    for prod_id, name, price, old_price, stock in products:
        price_text = format_price(price)
        if old_price and old_price > price:
            discount = int((1 - price/old_price) * 100)
            price_text = f"{format_price(old_price)} → {format_price(price)} (-{discount}%)"
        
        stock_icon = "✅" if stock > 0 else "❌"
        markup.add(InlineKeyboardButton(
            f"{stock_icon} {name} - {price_text} {get_setting('currency')}",
            callback_data=f"prod_{prod_id}"
        ))
    
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_categories"))
    
    await callback.message.edit_text(
        f"📁 <b>{cat_name[0] if cat_name else 'Kategoriya'}</b>\n\n"
        f"📦 Mahsulotlar soni: {len(products)}\n\n"
        "Mahsulotni tanlang:",
        reply_markup=markup,
        parse_mode='HTML'
    )

# Product details
@dp.callback_query_handler(lambda c: c.data.startswith('prod_'))
async def show_product_details(callback: types.CallbackQuery):
    prod_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    # Increment views
    c.execute('UPDATE products SET views = views + 1 WHERE id = ?', (prod_id,))
    
    c.execute('''SELECT p.name, p.description, p.price, p.old_price, p.sizes, p.image_id, p.stock, p.category_id, p.views,
                        c.name as category_name
                 FROM products p
                 LEFT JOIN categories c ON p.category_id = c.id
                 WHERE p.id = ?''', (prod_id,))
    product = c.fetchone()
    
    # Check if in wishlist
    c.execute('SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?', (user_id, prod_id))
    in_wishlist = c.fetchone() is not None
    
    # Get average rating
    c.execute('SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?', (prod_id,))
    rating_data = c.fetchone()
    avg_rating = rating_data[0] if rating_data[0] else 0
    review_count = rating_data[1]
    
    conn.commit()
    conn.close()
    
    if not product:
        await callback.answer("❌ Mahsulot topilmadi")
        return
    
    name, desc, price, old_price, sizes, image_id, stock, category_id, views, cat_name = product
    sizes_list = json.loads(sizes) if sizes else []
    
    text = f"📦 <b>{name}</b>\n\n"
    text += f"📁 Kategoriya: {cat_name}\n"
    text += f"📝 {desc}\n\n"
    
    if old_price and old_price > price:
        discount = int((1 - price/old_price) * 100)
        text += f"💰 Eski narx: <s>{format_price(old_price)}</s>\n"
        text += f"🔥 Yangi narx: <b>{format_price(price)} {get_setting('currency')}</b> (-{discount}%)\n"
    else:
        text += f"💰 Narx: <b>{format_price(price)} {get_setting('currency')}</b>\n"
    
    text += f"📦 Omborda: {stock} dona\n"
    text += f"👁 Ko'rishlar: {views}\n"
    
    if review_count > 0:
        stars = "⭐" * int(avg_rating)
        text += f"⭐ Reyting: {avg_rating:.1f}/5 {stars} ({review_count} sharh)\n"
    
    if sizes_list:
        text += f"📏 O'lchamlar: {', '.join(sizes_list)}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    if stock > 0:
        if sizes_list:
            for size in sizes_list:
                markup.insert(InlineKeyboardButton(
                    f"📏 {size}",
                    callback_data=f"addcart_{prod_id}_{size}"
                ))
        else:
            markup.row(InlineKeyboardButton("🛒 Savatga qo'shish", callback_data=f"addcart_{prod_id}_none"))
    else:
        markup.row(InlineKeyboardButton("❌ Omborda yo'q", callback_data="out_of_stock"))
    
    # Wishlist button
    wish_text = "💔 Sevimlilardan o'chirish" if in_wishlist else "❤️ Sevimliga qo'shish"
    markup.row(InlineKeyboardButton(wish_text, callback_data=f"togglewish_{prod_id}"))
    
    markup.row(
        InlineKeyboardButton("📊 Sharhlar", callback_data=f"reviews_{prod_id}"),
        InlineKeyboardButton("◀️ Orqaga", callback_data=f"cat_{category_id}")
    )
    
    if image_id:
        try:
            await callback.message.delete()
            await bot.send_photo(
                callback.from_user.id,
                image_id,
                caption=text,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')
    else:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Toggle wishlist
@dp.callback_query_handler(lambda c: c.data.startswith('togglewish_'))
async def toggle_wishlist(callback: types.CallbackQuery):
    prod_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    c.execute('SELECT id FROM wishlist WHERE user_id = ? AND product_id = ?', (user_id, prod_id))
    existing = c.fetchone()
    
    if existing:
        c.execute('DELETE FROM wishlist WHERE id = ?', (existing[0],))
        await callback.answer("💔 Sevimlilardan o'chirildi")
    else:
        c.execute('INSERT INTO wishlist (user_id, product_id) VALUES (?, ?)', (user_id, prod_id))
        await callback.answer("❤️ Sevimliga qo'shildi")
    
    conn.commit()
    conn.close()
    
    # Refresh product details
    await show_product_details(callback)

# Show wishlist
@dp.message_handler(lambda m: m.text == "❤️ Sevimlilar")
async def show_wishlist(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT p.id, p.name, p.price, p.stock
                 FROM wishlist w
                 JOIN products p ON w.product_id = p.id
                 WHERE w.user_id = ?
                 ORDER BY w.added_at DESC''', (message.from_user.id,))
    items = c.fetchall()
    conn.close()
    
    if not items:
        await message.answer("❤️ Sevimlilar ro'yxati bo'sh")
        return
    
    text = "❤️ <b>Sevimli mahsulotlar:</b>\n\n"
    markup = InlineKeyboardMarkup(row_width=1)
    
    for prod_id, name, price, stock in items:
        stock_icon = "✅" if stock > 0 else "❌"
        text += f"{stock_icon} {name} - {format_price(price)} {get_setting('currency')}\n"
        markup.add(InlineKeyboardButton(
            f"{name}",
            callback_data=f"prod_{prod_id}"
        ))
    
    markup.row(InlineKeyboardButton("🗑 Tozalash", callback_data="clear_wishlist"))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Clear wishlist
@dp.callback_query_handler(lambda c: c.data == 'clear_wishlist')
async def clear_wishlist(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('DELETE FROM wishlist WHERE user_id = ?', (callback.from_user.id,))
    conn.commit()
    conn.close()
    
    await callback.message.delete()
    await callback.message.answer("🗑 Sevimlilar ro'yxati tozalandi!")

# Add to cart
@dp.callback_query_handler(lambda c: c.data.startswith('addcart_'))
async def add_to_cart(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    prod_id = int(parts[1])
    size = parts[2] if len(parts) > 2 and parts[2] != 'none' else None
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    # Check stock
    c.execute('SELECT stock, name FROM products WHERE id = ?', (prod_id,))
    product = c.fetchone()
    
    if not product or product[0] <= 0:
        await callback.answer("❌ Mahsulot omborda yo'q!", show_alert=True)
        conn.close()
        return
    
    # Check if item already in cart
    c.execute('SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ? AND size = ?',
              (callback.from_user.id, prod_id, size))
    existing = c.fetchone()
    
    if existing:
        if existing[1] < product[0]:
            c.execute('UPDATE cart SET quantity = quantity + 1 WHERE id = ?', (existing[0],))
            await callback.answer("✅ Miqdor oshirildi!")
        else:
            await callback.answer("⚠️ Omborda yetarli mahsulot yo'q!", show_alert=True)
            conn.close()
            return
    else:
        c.execute('INSERT INTO cart (user_id, product_id, size) VALUES (?, ?, ?)',
                  (callback.from_user.id, prod_id, size))
        await callback.answer("✅ Savatga qo'shildi!")
    
    conn.commit()
    conn.close()

# Show cart
@dp.message_handler(lambda m: m.text == "🛒 Savat")
async def show_cart(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT c.id, p.id, p.name, p.price, c.quantity, c.size, p.stock
                 FROM cart c
                 JOIN products p ON c.product_id = p.id
                 WHERE c.user_id = ?
                 ORDER BY c.added_at DESC''', (message.from_user.id,))
    items = c.fetchall()
    conn.close()
    
    if not items:
        await message.answer("🛒 Savatingiz bo'sh")
        return
    
    text = "🛒 <b>Sizning savatingiz:</b>\n\n"
    total = 0
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    for cart_id, prod_id, name, price, qty, size, stock in items:
        item_total = price * qty
        total += item_total
        size_text = f" ({size})" if size else ""
        
        # Check if quantity exceeds stock
        warning = " ⚠️" if qty > stock else ""
        
        text += f"📦 <b>{name}</b>{size_text}{warning}\n"
        text += f"   💰 {qty} x {format_price(price)} = {format_price(item_total)} {get_setting('currency')}\n"
        
        # Quantity controls
        markup.row(
            InlineKeyboardButton("➖", callback_data=f"cartminus_{cart_id}"),
            InlineKeyboardButton(f"{qty}", callback_data=f"cartinfo_{cart_id}"),
            InlineKeyboardButton("➕", callback_data=f"cartplus_{cart_id}_{prod_id}_{stock}")
        )
        markup.row(InlineKeyboardButton(f"🗑 {name} o'chirish", callback_data=f"delcart_{cart_id}"))
        
        text += "\n"
    
    delivery_price = float(get_setting('delivery_price', '25000'))
    free_delivery_from = float(get_setting('free_delivery_from', '200000'))
    
    if total >= free_delivery_from:
        text += f"🚚 Yetkazib berish: <b>BEPUL</b>\n"
        final_total = total
    else:
        text += f"🚚 Yetkazib berish: {format_price(delivery_price)} {get_setting('currency')}\n"
        text += f"💡 {format_price(free_delivery_from)} {get_setting('currency')} dan yuqori buyurtmada yetkazib berish bepul!\n"
        final_total = total + delivery_price
    
    text += f"\n💰 <b>Jami: {format_price(final_total)} {get_setting('currency')}</b>"
    
    markup.row(InlineKeyboardButton("✅ Buyurtma berish", callback_data="checkout"))
    markup.row(InlineKeyboardButton("🗑 Savatni tozalash", callback_data="clear_cart"))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Cart quantity controls
@dp.callback_query_handler(lambda c: c.data.startswith('cartminus_'))
async def cart_decrease(callback: types.CallbackQuery):
    cart_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT quantity FROM cart WHERE id = ? AND user_id = ?', (cart_id, callback.from_user.id))
    result = c.fetchone()
    
    if result and result[0] > 1:
        c.execute('UPDATE cart SET quantity = quantity - 1 WHERE id = ?', (cart_id,))
        conn.commit()
        await callback.answer("✅ Miqdor kamaytirildi")
    else:
        c.execute('DELETE FROM cart WHERE id = ?', (cart_id,))
        conn.commit()
        await callback.answer("🗑 Mahsulot o'chirildi")
    
    conn.close()
    await show_cart(callback.message)

@dp.callback_query_handler(lambda c: c.data.startswith('cartplus_'))
async def cart_increase(callback: types.CallbackQuery):
    parts = callback.data.split('_')
    cart_id = int(parts[1])
    prod_id = int(parts[2])
    stock = int(parts[3])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT quantity FROM cart WHERE id = ? AND user_id = ?', (cart_id, callback.from_user.id))
    result = c.fetchone()
    
    if result and result[0] < stock:
        c.execute('UPDATE cart SET quantity = quantity + 1 WHERE id = ?', (cart_id,))
        conn.commit()
        await callback.answer("✅ Miqdor oshirildi")
    else:
        await callback.answer("⚠️ Omborda yetarli mahsulot yo'q!", show_alert=True)
    
    conn.close()
    await show_cart(callback.message)

# Delete from cart
@dp.callback_query_handler(lambda c: c.data.startswith('delcart_'))
async def delete_from_cart(callback: types.CallbackQuery):
    cart_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, callback.from_user.id))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ O'chirildi")
    await show_cart(callback.message)

# Clear cart
@dp.callback_query_handler(lambda c: c.data == 'clear_cart')
async def clear_cart(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('DELETE FROM cart WHERE user_id = ?', (callback.from_user.id,))
    conn.commit()
    conn.close()
    
    await callback.message.delete()
    await callback.message.answer("🗑 Savat tozalandi!")

# Checkout - Step 1: Delivery method
@dp.callback_query_handler(lambda c: c.data == 'checkout')
async def checkout_delivery(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM cart WHERE user_id = ?', (callback.from_user.id,))
    cart_count = c.fetchone()[0]
    conn.close()
    
    if cart_count == 0:
        await callback.answer("❌ Savat bo'sh!")
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🚚 Yetkazib berish", callback_data="delivery_courier"),
        InlineKeyboardButton("🏪 Olib ketish", callback_data="delivery_pickup")
    )
    markup.row(InlineKeyboardButton("◀️ Bekor qilish", callback_data="cancel_checkout"))
    
    await callback.message.edit_text(
        "🚚 <b>Yetkazib berish usulini tanlang:</b>",
        reply_markup=markup,
        parse_mode='HTML'
    )
    await OrderCheckout.delivery_method.set()

# Checkout - Delivery method selected
@dp.callback_query_handler(lambda c: c.data.startswith('delivery_'), state=OrderCheckout.delivery_method)
async def checkout_delivery_selected(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split('_')[1]
    await state.update_data(delivery_method=method)
    
    if method == "courier":
        await callback.message.edit_text(
            "📍 <b>Yetkazib berish manzilini kiriting:</b>\n\n"
            "Masalan: Toshkent, Yunusobod tumani, Amir Temur ko'chasi, 1-uy",
            parse_mode='HTML'
        )
        await OrderCheckout.delivery_address.set()
    else:
        await state.update_data(delivery_address="Olib ketish")
        await checkout_payment_method(callback, state)

# Checkout - Address
@dp.message_handler(state=OrderCheckout.delivery_address)
async def checkout_address(message: types.Message, state: FSMContext):
    await state.update_data(delivery_address=message.text)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💳 Karta", callback_data="payment_card"),
        InlineKeyboardButton("💵 Naqd", callback_data="payment_cash")
    )
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_delivery"))
    
    await message.answer(
        "💳 <b>To'lov usulini tanlang:</b>",
        reply_markup=markup,
        parse_mode='HTML'
    )
    await OrderCheckout.payment_method.set()

@dp.callback_query_handler(lambda c: c.data.startswith('payment_'), state=OrderCheckout.payment_method)
async def checkout_payment_method(callback: types.CallbackQuery, state: FSMContext):
    if isinstance(callback, types.CallbackQuery):
        method = callback.data.split('_')[1]
        await state.update_data(payment_method=method)
        
        await callback.message.edit_text(
            "📝 <b>Qo'shimcha izoh yoki xabar:</b>\n\n"
            "Agar qo'shimcha ma'lumot bo'lsa yozing, yo'q bo'lsa 0 deb yozing:",
            parse_mode='HTML'
        )
    else:
        # Called from pickup
        await state.update_data(payment_method="cash")
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("💳 Karta", callback_data="payment_card"),
            InlineKeyboardButton("💵 Naqd", callback_data="payment_cash")
        )
        
        await callback.message.edit_text(
            "💳 <b>To'lov usulini tanlang:</b>",
            reply_markup=markup,
            parse_mode='HTML'
        )
        await OrderCheckout.payment_method.set()
        return
    
    await OrderCheckout.notes.set()

# Checkout - Notes
@dp.message_handler(state=OrderCheckout.notes)
async def checkout_notes(message: types.Message, state: FSMContext):
    notes = message.text if message.text != "0" else ""
    await state.update_data(notes=notes)
    
    await message.answer(
        "🎁 <b>Promokod bormi?</b>\n\n"
        "Promokodni kiriting yoki 0 deb yozing:",
        parse_mode='HTML'
    )
    await OrderCheckout.promocode.set()

# Checkout - Promocode
@dp.message_handler(state=OrderCheckout.promocode)
async def checkout_promocode(message: types.Message, state: FSMContext):
    promocode_text = message.text.strip().upper()
    discount = 0
    promo_id = None
    
    if promocode_text != "0":
        conn = sqlite3.connect('shop.db')
        c = conn.cursor()
        
        # Check promocode
        c.execute('''SELECT id, discount_percent, discount_amount, max_uses, used_count
                     FROM promocodes
                     WHERE code = ? AND is_active = 1
                     AND datetime('now') BETWEEN datetime(valid_from) AND datetime(valid_until)''',
                  (promocode_text,))
        promo = c.fetchone()
        
        if promo:
            promo_id, discount_percent, discount_amount, max_uses, used_count = promo
            
            # Check if user already used
            c.execute('SELECT id FROM user_promocodes WHERE user_id = ? AND promocode_id = ?',
                      (message.from_user.id, promo_id))
            if c.fetchone():
                await message.answer("⚠️ Siz bu promokodni avval ishlatgansiz!")
                promo_id = None
            elif max_uses and used_count >= max_uses:
                await message.answer("⚠️ Promokod limitga yetdi!")
                promo_id = None
            else:
                if discount_percent:
                    discount = discount_percent
                elif discount_amount:
                    discount = discount_amount
                await message.answer(f"✅ Promokod qo'llandi! 🎉")
        else:
            await message.answer("❌ Promokod topilmadi yoki yaroqsiz!")
        
        conn.close()
    
    await state.update_data(promocode=promocode_text if promo_id else None, 
                           discount=discount, 
                           promocode_id=promo_id)
    
    # Show order summary
    data = await state.get_data()
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT p.name, p.price, c.quantity, c.size
                 FROM cart c
                 JOIN products p ON c.product_id = p.id
                 WHERE c.user_id = ?''', (message.from_user.id,))
    items = c.fetchall()
    conn.close()
    
    text = "📋 <b>Buyurtma ma'lumotlari:</b>\n\n"
    subtotal = 0
    
    for name, price, qty, size in items:
        item_total = price * qty
        subtotal += item_total
        size_text = f" ({size})" if size else ""
        text += f"📦 {name}{size_text} x {qty}\n"
        text += f"   💰 {format_price(item_total)} {get_setting('currency')}\n"
    
    text += f"\n💰 Oraliq summa: {format_price(subtotal)} {get_setting('currency')}\n"
    
    # Apply discount
    discount_amount = 0
    if discount:
        if discount < 100:  # Percentage
            discount_amount = subtotal * discount / 100
            text += f"🎁 Chegirma ({discount}%): -{format_price(discount_amount)} {get_setting('currency')}\n"
        else:  # Fixed amount
            discount_amount = min(discount, subtotal)
            text += f"🎁 Chegirma: -{format_price(discount_amount)} {get_setting('currency')}\n"
    
    subtotal -= discount_amount
    
    # Delivery
    delivery_price = 0
    if data['delivery_method'] == 'courier':
        free_delivery_from = float(get_setting('free_delivery_from', '200000'))
        if subtotal >= free_delivery_from:
            text += f"🚚 Yetkazib berish: BEPUL\n"
        else:
            delivery_price = float(get_setting('delivery_price', '25000'))
            text += f"🚚 Yetkazib berish: {format_price(delivery_price)} {get_setting('currency')}\n"
    
    total = subtotal + delivery_price
    
    text += f"\n💰 <b>Jami to'lov: {format_price(total)} {get_setting('currency')}</b>\n\n"
    text += f"🚚 Yetkazib berish: {data['delivery_method']}\n"
    if data['delivery_method'] == 'courier':
        text += f"📍 Manzil: {data['delivery_address']}\n"
    text += f"💳 To'lov: {data['payment_method']}\n"
    
    if data.get('notes'):
        text += f"📝 Izoh: {data['notes']}\n"
    
    payment_method = data['payment_method']
    
    if payment_method == 'card':
        card_number = get_setting('card_number')
        card_owner = get_setting('card_owner')
        
        text += f"\n💳 <b>To'lov ma'lumotlari:</b>\n"
        text += f"🏦 Karta: <code>{card_number}</code>\n"
        text += f"👤 Egasi: {card_owner}\n\n"
        text += "📸 To'lovni amalga oshirgach, chek rasmini yuboring!"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("◀️ Bekor qilish", callback_data="cancel_checkout"))
        
        await message.answer(text, reply_markup=markup, parse_mode='HTML')
        await OrderCheckout.payment_check.set()
    else:
        # Cash payment - create order immediately
        await create_order(message, state, None, total, discount_amount)

# Create order helper
async def create_order(message, state, photo_id, total, discount_amount):
    data = await state.get_data()
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    # Get cart items
    c.execute('''SELECT p.id, p.name, p.price, c.quantity, c.size
                 FROM cart c
                 JOIN products p ON c.product_id = p.id
                 WHERE c.user_id = ?''', (message.from_user.id,))
    items = c.fetchall()
    
    # Create order
    order_number = generate_order_number()
    items_json = json.dumps([{
        'product_id': pid,
        'name': name,
        'price': price,
        'quantity': qty,
        'size': size
    } for pid, name, price, qty, size in items])
    
    c.execute('''INSERT INTO orders (order_number, user_id, items, total_price, payment_check,
                                     delivery_address, delivery_method, payment_method, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (order_number, message.from_user.id, items_json, total, photo_id,
               data.get('delivery_address'), data.get('delivery_method'), 
               data.get('payment_method'), data.get('notes')))
    
    # Update stock
    for pid, _, _, qty, _ in items:
        c.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (qty, pid))
    
    # Clear cart
    c.execute('DELETE FROM cart WHERE user_id = ?', (message.from_user.id,))
    
    # Apply promocode
    if data.get('promocode_id'):
        c.execute('INSERT INTO user_promocodes (user_id, promocode_id) VALUES (?, ?)',
                  (message.from_user.id, data['promocode_id']))
        c.execute('UPDATE promocodes SET used_count = used_count + 1 WHERE id = ?',
                  (data['promocode_id'],))
    
    # Get user info
    c.execute('SELECT full_name, phone FROM users WHERE user_id = ?', (message.from_user.id,))
    user_info = c.fetchone()
    
    # Add notification
    c.execute('''INSERT INTO notifications (user_id, title, message)
                 VALUES (?, ?, ?)''',
              (message.from_user.id, "✅ Buyurtma qabul qilindi",
               f"📦 Buyurtma #{order_number}\n💰 Summa: {format_price(total)} {get_setting('currency')}\nTez orada siz bilan bog'lanamiz!"))
    
    conn.commit()
    conn.close()
    
    await state.finish()
    
    # Send confirmation to user
    await message.answer(
        f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
        f"📦 Buyurtma raqami: <code>{order_number}</code>\n"
        f"💰 Summa: {format_price(total)} {get_setting('currency')}\n\n"
        f"📞 Tez orada siz bilan bog'lanamiz!",
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )
    
    # Notify admins
    admin_text = f"🆕 <b>Yangi buyurtma!</b>\n\n"
    admin_text += f"📦 Raqam: <code>{order_number}</code>\n"
    admin_text += f"👤 Mijoz: {user_info[0]}\n"
    admin_text += f"📱 Telefon: {user_info[1]}\n"
    admin_text += f"🚚 Yetkazish: {data.get('delivery_method')}\n"
    if data.get('delivery_method') == 'courier':
        admin_text += f"📍 Manzil: {data.get('delivery_address')}\n"
    admin_text += f"💳 To'lov: {data.get('payment_method')}\n"
    if data.get('notes'):
        admin_text += f"📝 Izoh: {data.get('notes')}\n"
    admin_text += f"💰 Summa: {format_price(total)} {get_setting('currency')}\n"
    if discount_amount > 0:
        admin_text += f"🎁 Chegirma: {format_price(discount_amount)} {get_setting('currency')}\n"
    admin_text += "\n<b>Mahsulotlar:</b>\n"
    
    for _, name, price, qty, size in items:
        size_text = f" ({size})" if size else ""
        admin_text += f"• {name}{size_text} x {qty} = {format_price(price * qty)} {get_setting('currency')}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_order_{order_number}"))
    markup.add(InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_order_{order_number}"))
    markup.add(InlineKeyboardButton("💬 Mijoz bilan chat", callback_data=f"chat_{message.from_user.id}"))
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM admins')
    admins = c.fetchall()
    conn.close()
    
    for (admin_id,) in admins:
        try:
            if photo_id:
                await bot.send_photo(admin_id, photo_id, caption=admin_text, reply_markup=markup, parse_mode='HTML')
            else:
                await bot.send_message(admin_id, admin_text, reply_markup=markup, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Error sending to admin {admin_id}: {e}")

# Payment check handler
@dp.message_handler(content_types=['photo'], state=OrderCheckout.payment_check)
async def process_payment_check(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT SUM(p.price * c.quantity)
                 FROM cart c
                 JOIN products p ON c.product_id = p.id
                 WHERE c.user_id = ?''', (message.from_user.id,))
    subtotal = c.fetchone()[0] or 0
    conn.close()
    
    # Calculate total
    discount_amount = 0
    if data.get('discount'):
        discount = data['discount']
        if discount < 100:
            discount_amount = subtotal * discount / 100
        else:
            discount_amount = min(discount, subtotal)
    
    subtotal -= discount_amount
    
    delivery_price = 0
    if data['delivery_method'] == 'courier':
        free_delivery_from = float(get_setting('free_delivery_from', '200000'))
        if subtotal < free_delivery_from:
            delivery_price = float(get_setting('delivery_price', '25000'))
    
    total = subtotal + delivery_price
    
    await create_order(message, state, photo_id, total, discount_amount)

# Cancel checkout
@dp.callback_query_handler(lambda c: c.data == 'cancel_checkout', state='*')
async def cancel_checkout(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()
    await callback.message.answer("❌ Buyurtma bekor qilindi", reply_markup=get_main_keyboard())

# Admin order confirmation
@dp.callback_query_handler(lambda c: c.data.startswith('confirm_order_'))
async def confirm_order(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    
    order_number = callback.data.split('_', 2)[2]
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_number = ?', 
              ('confirmed', order_number))
    c.execute('SELECT user_id FROM orders WHERE order_number = ?', (order_number,))
    user_id = c.fetchone()[0]
    
    # Add notification
    c.execute('''INSERT INTO notifications (user_id, title, message)
                 VALUES (?, ?, ?)''',
              (user_id, "✅ Buyurtma tasdiqlandi",
               f"Buyurtma #{order_number} tasdiqlandi! Yetkazib berish bo'yicha tez orada bog'lanamiz."))
    
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Buyurtma tasdiqlandi!")
    await callback.message.edit_reply_markup(reply_markup=None)
    
    try:
        await bot.send_message(
            user_id,
            f"✅ <b>Buyurtmangiz tasdiqlandi!</b>\n\n"
            f"📦 Buyurtma raqami: <code>{order_number}</code>\n"
            f"🚚 Yetkazib berish bo'yicha tez orada bog'lanamiz.",
            parse_mode='HTML'
        )
    except:
        pass

# Cancel order
@dp.callback_query_handler(lambda c: c.data.startswith('cancel_order_'))
async def cancel_order_admin(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    
    order_number = callback.data.split('_', 2)[2]
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    # Get order items to restore stock
    c.execute('SELECT items FROM orders WHERE order_number = ?', (order_number,))
    items_json = c.fetchone()[0]
    items = json.loads(items_json)
    
    # Restore stock
    for item in items:
        c.execute('UPDATE products SET stock = stock + ? WHERE id = ?', 
                  (item['quantity'], item['product_id']))
    
    c.execute('UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_number = ?', 
              ('cancelled', order_number))
    c.execute('SELECT user_id FROM orders WHERE order_number = ?', (order_number,))
    user_id = c.fetchone()[0]
    
    # Add notification
    c.execute('''INSERT INTO notifications (user_id, title, message)
                 VALUES (?, ?, ?)''',
              (user_id, "❌ Buyurtma bekor qilindi",
               f"Buyurtma #{order_number} bekor qilindi. Batafsil ma'lumot uchun bog'laning."))
    
    conn.commit()
    conn.close()
    
    await callback.answer("❌ Buyurtma bekor qilindi!")
    await callback.message.edit_reply_markup(reply_markup=None)
    
    try:
        await bot.send_message(
            user_id,
            f"❌ <b>Buyurtmangiz bekor qilindi</b>\n\n"
            f"📦 Buyurtma raqami: <code>{order_number}</code>\n"
            f"📞 Batafsil ma'lumot uchun bog'laning.",
            parse_mode='HTML'
        )
    except:
        pass

# Deliver order
@dp.callback_query_handler(lambda c: c.data.startswith('deliver_order_'))
async def deliver_order(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    
    order_number = callback.data.split('_', 2)[2]
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_number = ?', 
              ('delivered', order_number))
    c.execute('SELECT user_id FROM orders WHERE order_number = ?', (order_number,))
    user_id = c.fetchone()[0]
    
    # Add notification
    c.execute('''INSERT INTO notifications (user_id, title, message)
                 VALUES (?, ?, ?)''',
              (user_id, "🚚 Buyurtma yetkazildi",
               f"Buyurtma #{order_number} yetkazildi! Xaridingiz uchun rahmat!"))
    
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Buyurtma yetkazildi deb belgilandi!")
    
    try:
        await bot.send_message(
            user_id,
            f"🚚 <b>Buyurtmangiz yetkazildi!</b>\n\n"
            f"📦 Buyurtma raqami: <code>{order_number}</code>\n\n"
            f"Xaridingiz uchun rahmat! 😊\n\n"
            f"Iltimos, mahsulot haqida sharh qoldiring!",
            parse_mode='HTML'
        )
    except:
        pass

# Chat with user
@dp.callback_query_handler(lambda c: c.data.startswith('chat_'))
async def start_chat_with_user(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    
    user_id = int(callback.data.split('_')[1])
    
    await state.update_data(chat_user_id=user_id)
    await ChatWithUser.message.set()
    
    await callback.message.answer(
        f"💬 <b>Chat boshlandi</b>\n\n"
        f"User ID: <code>{user_id}</code>\n\n"
        f"Xabar yozing yoki /cancel",
        parse_mode='HTML'
    )

# Send message to user from admin
@dp.message_handler(state=ChatWithUser.message, content_types=types.ContentTypes.ANY)
async def send_message_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('chat_user_id')
    
    try:
        await message.copy_to(user_id)
        await message.answer("✅ Xabar yuborildi!")
    except Exception as e:
        await message.answer(f"❌ Xabar yuborishda xatolik: {str(e)}")
    
    await state.finish()

# My orders
@dp.message_handler(lambda m: m.text == "📦 Buyurtmalarim")
async def my_orders(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT order_number, total_price, status, created_at 
                 FROM orders 
                 WHERE user_id = ? 
                 ORDER BY created_at DESC 
                 LIMIT 20''',
              (message.from_user.id,))
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("📦 Sizda buyurtmalar yo'q")
        return
    
    text = "📦 <b>Sizning buyurtmalaringiz:</b>\n\n"
    
    status_emoji = {
        'pending': '⏳',
        'confirmed': '✅',
        'cancelled': '❌',
        'delivered': '🚚'
    }
    
    status_text = {
        'pending': 'Kutilmoqda',
        'confirmed': 'Tasdiqlangan',
        'cancelled': 'Bekor qilingan',
        'delivered': 'Yetkazilgan'
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for order_num, total, status, created in orders:
        emoji = status_emoji.get(status, '❓')
        status_name = status_text.get(status, status)
        
        text += f"{emoji} <b>{order_num}</b>\n"
        text += f"   💰 {format_price(total)} {get_setting('currency')} | {status_name}\n"
        text += f"   📅 {created[:16]}\n\n"
        
        markup.add(InlineKeyboardButton(
            f"{emoji} {order_num}",
            callback_data=f"order_details_{order_num}"
        ))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Order details
@dp.callback_query_handler(lambda c: c.data.startswith('order_details_'))
async def order_details(callback: types.CallbackQuery):
    order_number = callback.data.split('_', 2)[2]
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT items, total_price, status, created_at, delivery_address, 
                        delivery_method, payment_method, notes
                 FROM orders WHERE order_number = ?''',
              (order_number,))
    order = c.fetchone()
    conn.close()
    
    if not order:
        await callback.answer("❌ Buyurtma topilmadi")
        return
    
    items_json, total, status, created, address, delivery, payment, notes = order
    items = json.loads(items_json)
    
    status_text = {
        'pending': '⏳ Kutilmoqda',
        'confirmed': '✅ Tasdiqlangan',
        'cancelled': '❌ Bekor qilingan',
        'delivered': '🚚 Yetkazilgan'
    }
    
    text = f"📋 <b>Buyurtma #{order_number}</b>\n\n"
    text += f"📅 Sana: {created[:16]}\n"
    text += f"📊 Holat: {status_text.get(status, status)}\n"
    text += f"🚚 Yetkazish: {delivery}\n"
    if delivery == 'courier':
        text += f"📍 Manzil: {address}\n"
    text += f"💳 To'lov: {payment}\n"
    if notes:
        text += f"📝 Izoh: {notes}\n"
    text += "\n<b>Mahsulotlar:</b>\n"
    
    for item in items:
        size_text = f" ({item['size']})" if item.get('size') else ""
        text += f"• {item['name']}{size_text}\n"
        text += f"  {item['quantity']} x {format_price(item['price'])} = {format_price(item['price'] * item['quantity'])} {get_setting('currency')}\n"
    
    text += f"\n💰 <b>Jami: {format_price(total)} {get_setting('currency')}</b>"
    
    markup = InlineKeyboardMarkup()
    
    # Add review button for delivered orders
    if status == 'delivered':
        for item in items:
            markup.add(InlineKeyboardButton(
                f"⭐ {item['name']} haqida sharh",
                callback_data=f"review_{item['product_id']}"
            ))
    
    markup.add(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_orders"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Reviews
@dp.callback_query_handler(lambda c: c.data.startswith('review_'))
async def start_review(callback: types.CallbackQuery, state: FSMContext):
    prod_id = int(callback.data.split('_')[1])
    
    # Check if already reviewed
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT id FROM reviews WHERE user_id = ? AND product_id = ?',
              (callback.from_user.id, prod_id))
    if c.fetchone():
        await callback.answer("✅ Siz bu mahsulot haqida sharh qoldirgansiz!", show_alert=True)
        conn.close()
        return
    
    c.execute('SELECT name FROM products WHERE id = ?', (prod_id,))
    product_name = c.fetchone()[0]
    conn.close()
    
    await state.update_data(review_product_id=prod_id)
    
    markup = InlineKeyboardMarkup(row_width=5)
    markup.add(*[InlineKeyboardButton(f"{'⭐' * i}", callback_data=f"rating_{i}") for i in range(1, 6)])
    markup.row(InlineKeyboardButton("◀️ Bekor qilish", callback_data="cancel_review"))
    
    await callback.message.edit_text(
        f"⭐ <b>{product_name} uchun baho bering:</b>\n\n"
        "1 dan 5 gacha baholang:",
        reply_markup=markup,
        parse_mode='HTML'
    )
    await LeaveReview.rating.set()

@dp.callback_query_handler(lambda c: c.data.startswith('rating_'), state=LeaveReview.rating)
async def review_rating(callback: types.CallbackQuery, state: FSMContext):
    rating = int(callback.data.split('_')[1])
    await state.update_data(review_rating=rating)
    
    await callback.message.edit_text(
        f"⭐ Baho: {'⭐' * rating}\n\n"
        "📝 Endi sharh yozing (yoki 0 - sharh yo'q):",
        parse_mode='HTML'
    )
    await LeaveReview.comment.set()

@dp.message_handler(state=LeaveReview.comment)
async def review_comment(message: types.Message, state: FSMContext):
    comment = message.text if message.text != "0" else ""
    data = await state.get_data()
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''INSERT INTO reviews (user_id, product_id, rating, comment)
                 VALUES (?, ?, ?, ?)''',
              (message.from_user.id, data['review_product_id'], data['review_rating'], comment))
    conn.commit()
    conn.close()
    
    await state.finish()
    
    await message.answer(
        "✅ <b>Rahmat! Sharhingiz qabul qilindi.</b>\n\n"
        "⭐ Sizning fikringiz bizga muhim!",
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )

@dp.callback_query_handler(lambda c: c.data == 'cancel_review', state=LeaveReview.rating)
async def cancel_review(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()
    await callback.message.answer("❌ Bekor qilindi", reply_markup=get_main_keyboard())

# Show reviews for product
@dp.callback_query_handler(lambda c: c.data.startswith('reviews_'))
async def show_reviews(callback: types.CallbackQuery):
    prod_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT name FROM products WHERE id = ?', (prod_id,))
    product_name = c.fetchone()[0]
    
    c.execute('''SELECT r.rating, r.comment, r.created_at, u.full_name
                 FROM reviews r
                 JOIN users u ON r.user_id = u.user_id
                 WHERE r.product_id = ?
                 ORDER BY r.created_at DESC
                 LIMIT 10''', (prod_id,))
    reviews = c.fetchall()
    
    c.execute('SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?', (prod_id,))
    avg_rating, count = c.fetchone()
    
    conn.close()
    
    text = f"⭐ <b>Sharhlar: {product_name}</b>\n\n"
    
    if count > 0:
        stars = "⭐" * int(avg_rating)
        text += f"📊 O'rtacha: {avg_rating:.1f}/5 {stars}\n"
        text += f"📝 Jami sharhlar: {count}\n\n"
        
        for rating, comment, created, name in reviews:
            text += f"👤 {name}\n"
            text += f"⭐ {'⭐' * rating} ({rating}/5)\n"
            if comment:
                text += f"💬 {comment}\n"
            text += f"📅 {created[:10]}\n\n"
    else:
        text += "Hozircha sharhlar yo'q 😔"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("◀️ Orqaga", callback_data=f"prod_{prod_id}"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Referral system
@dp.message_handler(lambda m: m.text == "💎 Referal")
async def referral_menu(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
    referrals_count = c.fetchone()[0]
    
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = c.fetchone()[0]
    
    bonus = get_setting('referral_bonus', '5000')
    gift_points = get_setting('referral_gift_points', '50000')
    
    conn.close()
    
    bot_username = (await bot.me).username
    ref_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    text = f"💎 <b>Referal tizimi</b>\n\n"
    text += f"🔗 Sizning havolangiz:\n<code>{ref_link}</code>\n\n"
    text += f"👥 Do'stlaringiz soni: {referrals_count}\n"
    text += f"💰 Balansingiz: {format_price(balance)} {get_setting('currency')}\n\n"
    text += f"🎁 Har bir do'st uchun: {format_price(int(bonus))} {get_setting('currency')}\n"
    text += f"🎁 {format_price(int(gift_points))} {get_setting('currency')}ga sovg'a olishingiz mumkin!\n\n"
    text += "📤 Havolangizni do'stlaringizga ulashing!"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📤 Ulashish", switch_inline_query=f"Salom! Bu ajoyib do'konga qo'shiling: {ref_link}"),
        InlineKeyboardButton("🎁 Sovg'a olish", callback_data="claim_gift")
    )
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Claim gift
@dp.callback_query_handler(lambda c: c.data == "claim_gift")
async def claim_gift(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = c.fetchone()[0]
    
    gift_points = int(get_setting('referral_gift_points', '50000'))
    
    if balance < gift_points:
        await callback.answer(
            f"❌ Yetarli emas! Kerak: {format_price(gift_points)} {get_setting('currency')}",
            show_alert=True
        )
        conn.close()
        return
    
    c.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (gift_points, user_id))
    conn.commit()
    conn.close()
    
    # Notify admins
    admin_text = f"🎁 <b>Sovg'a so'rovi!</b>\n\n"
    admin_text += f"👤 User ID: <code>{user_id}</code>\n"
    admin_text += f"💰 Ballar: {format_price(gift_points)} {get_setting('currency')}\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💬 Chat", callback_data=f"chat_{user_id}"))
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM admins')
    admins = c.fetchall()
    conn.close()
    
    for (admin_id,) in admins:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=markup, parse_mode='HTML')
        except:
            pass
    
    await callback.answer("✅ So'rov yuborildi! Admin siz bilan bog'lanadi.", show_alert=True)

# User statistics
@dp.message_handler(lambda m: m.text == "📊 Statistika")
async def user_statistics(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*), SUM(total_price) FROM orders WHERE user_id = ?', (user_id,))
    orders_count, total_spent = c.fetchone()
    total_spent = total_spent or 0
    
    c.execute('SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = "delivered"', (user_id,))
    delivered_count = c.fetchone()[0]
    
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
    referrals = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM reviews WHERE user_id = ?', (user_id,))
    reviews_count = c.fetchone()[0]
    
    c.execute('SELECT registered_at FROM users WHERE user_id = ?', (user_id,))
    registered = c.fetchone()[0]
    
    conn.close()
    
    text = f"📊 <b>Sizning statistikangiz:</b>\n\n"
    text += f"📅 Ro'yxatdan o'tgan: {registered[:10]}\n"
    text += f"📦 Jami buyurtmalar: {orders_count}\n"
    text += f"✅ Yetkazilgan: {delivered_count}\n"
    text += f"💰 Jami xarajat: {format_price(total_spent)} {get_setting('currency')}\n"
    text += f"💎 Balans: {format_price(balance)} {get_setting('currency')}\n"
    text += f"👥 Referallar: {referrals}\n"
    text += f"⭐ Sharhlar: {reviews_count}\n"
    
    await message.answer(text, parse_mode='HTML')

# ADMIN PANEL
@dp.message_handler(lambda m: m.text == "📊 Statistika" and is_admin(m.from_user.id))
async def admin_statistics(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM users WHERE DATE(registered_at) = DATE("now")')
    today_users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM users WHERE DATE(registered_at) >= DATE("now", "-7 days")')
    week_users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orders')
    total_orders = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
    pending_orders = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orders WHERE status = "confirmed"')
    confirmed_orders = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orders WHERE status = "delivered"')
    delivered_orders = c.fetchone()[0]
    
    c.execute('SELECT SUM(total_price) FROM orders WHERE status IN ("confirmed", "delivered")')
    result = c.fetchone()[0]
    total_revenue = result if result else 0
    
    c.execute('SELECT SUM(total_price) FROM orders WHERE status IN ("confirmed", "delivered") AND DATE(created_at) = DATE("now")')
    result = c.fetchone()[0]
    today_revenue = result if result else 0
    
    c.execute('SELECT COUNT(*) FROM products')
    total_products = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM products WHERE stock > 0')
    in_stock = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM categories')
    total_categories = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM reviews')
    total_reviews = c.fetchone()[0]
    
    c.execute('SELECT AVG(rating) FROM reviews')
    avg_rating = c.fetchone()[0] or 0
    
    conn.close()
    
    text = "📊 <b>Admin Statistika</b>\n\n"
    text += "<b>👥 Foydalanuvchilar:</b>\n"
    text += f"  • Jami: {total_users}\n"
    text += f"  • Bugun: {today_users}\n"
    text += f"  • Hafta: {week_users}\n\n"
    
    text += "<b>📦 Buyurtmalar:</b>\n"
    text += f"  • Jami: {total_orders}\n"
    text += f"  • ⏳ Kutilayotgan: {pending_orders}\n"
    text += f"  • ✅ Tasdiqlangan: {confirmed_orders}\n"
    text += f"  • 🚚 Yetkazilgan: {delivered_orders}\n\n"
    
    text += "<b>💰 Daromad:</b>\n"
    text += f"  • Jami: {format_price(total_revenue)} {get_setting('currency')}\n"
    text += f"  • Bugun: {format_price(today_revenue)} {get_setting('currency')}\n\n"
    
    text += "<b>📁 Mahsulotlar:</b>\n"
    text += f"  • Kategoriyalar: {total_categories}\n"
    text += f"  • Mahsulotlar: {total_products}\n"
    text += f"  • Omborda: {in_stock}\n\n"
    
    text += "<b>⭐ Sharhlar:</b>\n"
    text += f"  • Jami: {total_reviews}\n"
    text += f"  • O'rtacha: {avg_rating:.1f}/5\n"
    
    await message.answer(text, parse_mode='HTML')

# Broadcast
@dp.message_handler(lambda m: m.text == "📢 Reklama" and is_admin(m.from_user.id))
async def start_broadcast(message: types.Message):
    await message.answer(
        "📢 <b>Reklama yuborish</b>\n\n"
        "Barcha foydalanuvchilarga yuborilishi kerak bo'lgan xabarni yozing:\n"
        "(Matn, rasm, video, audio qo'llab-quvvatlanadi)\n\n"
        "Bekor qilish: /cancel",
        parse_mode='HTML'
    )
    await SendBroadcast.message.set()

@dp.message_handler(state=SendBroadcast.message, content_types=types.ContentTypes.ANY)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    await state.update_data(broadcast_message=message)
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE is_blocked = 0')
    user_count = c.fetchone()[0]
    conn.close()
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Ha, yuborish", callback_data="confirm_broadcast"),
        InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data="cancel_broadcast")
    )
    
    await message.answer(
        f"📢 <b>Tasdiqlash</b>\n\n"
        f"Xabar {user_count} ta foydalanuvchiga yuboriladi.\n\n"
        f"Davom etasizmi?",
        reply_markup=markup,
        parse_mode='HTML'
    )
    await SendBroadcast.confirm.set()

@dp.callback_query_handler(lambda c: c.data == 'confirm_broadcast', state=SendBroadcast.confirm)
async def confirm_broadcast(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    broadcast_msg = data['broadcast_message']
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE is_blocked = 0')
    users = c.fetchall()
    conn.close()
    
    await callback.message.edit_text("📤 Yuborilmoqda...")
    
    success = 0
    failed = 0
    blocked = 0
    
    for (user_id,) in users:
        try:
            await broadcast_msg.copy_to(user_id)
            success += 1
            await asyncio.sleep(0.05)  # Avoid hitting rate limits
        except Exception as e:
            if "blocked" in str(e).lower():
                blocked += 1
                # Mark user as blocked
                conn = sqlite3.connect('shop.db')
                c = conn.cursor()
                c.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
                conn.commit()
                conn.close()
            else:
                failed += 1
    
    await state.finish()
    await callback.message.edit_text(
        f"✅ <b>Reklama yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"🚫 Bloklangan: {blocked}\n"
        f"❌ Xatolik: {failed}",
        parse_mode='HTML'
    )

@dp.callback_query_handler(lambda c: c.data == 'cancel_broadcast', state=SendBroadcast.confirm)
async def cancel_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("❌ Reklama bekor qilindi")

# Categories management
@dp.message_handler(lambda m: m.text == "📁 Kategoriyalar" and is_admin(m.from_user.id))
async def manage_categories(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT id, name, description, is_active FROM categories ORDER BY name')
    categories = c.fetchall()
    conn.close()
    
    text = "📁 <b>Kategoriyalar boshqaruvi</b>\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    if categories:
        for cat_id, name, desc, is_active in categories:
            status = "✅" if is_active else "❌"
            markup.add(InlineKeyboardButton(
                f"{status} {name}",
                callback_data=f"editcat_{cat_id}"
            ))
    else:
        text += "Kategoriyalar yo'q\n\n"
    
    markup.add(InlineKeyboardButton("➕ Yangi kategoriya", callback_data="add_category"))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Add category
@dp.callback_query_handler(lambda c: c.data == "add_category")
async def add_category_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📁 <b>Yangi kategoriya</b>\n\n"
        "Kategoriya nomini kiriting:",
        parse_mode='HTML'
    )
    await AddCategory.name.set()
#manbaa @krv_coder
@dp.message_handler(state=AddCategory.name)
async def add_category_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Kategoriya tavsifini kiriting:")
    await AddCategory.description.set()

@dp.message_handler(state=AddCategory.description)
async def add_category_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    description = message.text
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
    conn.commit()
    conn.close()
    
    await state.finish()
    await message.answer(
        f"✅ Kategoriya qo'shildi!\n\n"
        f"📁 {name}\n"
        f"📝 {description}",
        reply_markup=get_admin_keyboard()
    )

# Edit category
@dp.callback_query_handler(lambda c: c.data.startswith('editcat_'))
async def edit_category(callback: types.CallbackQuery):
    cat_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT name, description, is_active FROM categories WHERE id = ?', (cat_id,))
    category = c.fetchone()
    conn.close()
    
    if not category:
        await callback.answer("❌ Kategoriya topilmadi")
        return
    #manbaa @krv_coder
    name, desc, is_active = category
    status = "✅ Faol" if is_active else "❌ Nofaol"
    
    text = f"📁 <b>{name}</b>\n\n"
    text += f"📝 {desc}\n"
    text += f"📊 Holat: {status}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    toggle_text = "❌ Faolsizlantirish" if is_active else "✅ Faollashtirish"
    markup.add(
        InlineKeyboardButton(toggle_text, callback_data=f"togglecat_{cat_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"delcat_{cat_id}")
    )
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_categories_admin"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Toggle category status
@dp.callback_query_handler(lambda c: c.data.startswith('togglecat_'))
async def toggle_category(callback: types.CallbackQuery):
    cat_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE categories SET is_active = NOT is_active WHERE id = ?', (cat_id,))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Holat o'zgartirildi")
    await edit_category(callback)

# Delete category
@dp.callback_query_handler(lambda c: c.data.startswith('delcat_'))
async def delete_category(callback: types.CallbackQuery):
    cat_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    # Check if category has products
    c.execute('SELECT COUNT(*) FROM products WHERE category_id = ?', (cat_id,))
    product_count = c.fetchone()[0]
    
    if product_count > 0:
        await callback.answer(
            f"❌ Bu kategoriyada {product_count} ta mahsulot bor! Avval mahsulotlarni o'chiring.",
            show_alert=True
        )
        conn.close()
        return
    
    c.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Kategoriya o'chirildi")
    await callback.message.delete()

# Products management
@dp.message_handler(lambda m: m.text == "📦 Mahsulotlar" and is_admin(m.from_user.id))
async def manage_products(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT p.id, p.name, p.price, c.name, p.stock, p.is_active 
                 FROM products p 
                 LEFT JOIN categories c ON p.category_id = c.id 
                 ORDER BY p.created_at DESC
                 LIMIT 20''')
    products = c.fetchall()
    conn.close()
    
    text = "📦 <b>Mahsulotlar boshqaruvi</b>\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    if products:
        for prod_id, name, price, cat_name, stock, is_active in products:
            status = "✅" if is_active else "❌"
            stock_icon = "📦" if stock > 0 else "🚫"
            markup.add(InlineKeyboardButton(
                f"{status} {name} - {format_price(price)} {get_setting('currency')} {stock_icon}{stock}",
                callback_data=f"editprod_{prod_id}"
            ))
    else:
        text += "Mahsulotlar yo'q\n\n"
    
    markup.add(InlineKeyboardButton("➕ Yangi mahsulot", callback_data="add_product"))
    markup.add(InlineKeyboardButton("🔍 Qidiruv", switch_inline_query_current_chat="admin:"))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Add product
@dp.callback_query_handler(lambda c: c.data == "add_product")
async def add_product_start(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name')
    categories = c.fetchall()
    conn.close()
    
    if not categories:
        await callback.answer("❌ Avval kategoriya qo'shing!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    for cat_id, name in categories:
        markup.insert(InlineKeyboardButton(name, callback_data=f"addprod_cat_{cat_id}"))
    markup.row(InlineKeyboardButton("◀️ Bekor qilish", callback_data="cancel_add_product"))
    
    await callback.message.edit_text(
        "📦 <b>Yangi mahsulot</b>\n\n"
        "Kategoriyani tanlang:",
        reply_markup=markup,
        parse_mode='HTML'
    )

@dp.callback_query_handler(lambda c: c.data.startswith('addprod_cat_'))
async def add_product_category(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split('_')[2])
    await state.update_data(category_id=cat_id)
    #manbaa @krv_coder
    
    await callback.message.edit_text(
        "📝 Mahsulot nomini kiriting:"
    )
    await AddProduct.name.set()

@dp.message_handler(state=AddProduct.name)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Mahsulot tavsifini kiriting:")
    await AddProduct.description.set()

@dp.message_handler(state=AddProduct.description)
async def add_product_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("💰 Narxni kiriting (so'm):")
    await AddProduct.price.set()

@dp.message_handler(state=AddProduct.price)
async def add_product_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await message.answer(
            "🔥 Eski narx bormi? (chegirma ko'rsatish uchun)\n"
            "Agar yo'q bo'lsa 0 deb yozing:"
        )
        await AddProduct.old_price.set()
    except:
        await message.answer("❌ Noto'g'ri format! Raqam kiriting:")

@dp.message_handler(state=AddProduct.old_price)
async def add_product_old_price(message: types.Message, state: FSMContext):
    try:
        old_price = float(message.text) if message.text != "0" else None
        await state.update_data(old_price=old_price)
        await message.answer(
            "📏 O'lchamlarni kiriting (vergul bilan ajratib: S,M,L,XL)\n"
            "Agar o'lcham kerak bo'lmasa, 0 deb yozing:"
        )
        await AddProduct.sizes.set()
    except:
        await message.answer("❌ Noto'g'ri format! Raqam kiriting:")

@dp.message_handler(state=AddProduct.sizes)
async def add_product_sizes(message: types.Message, state: FSMContext):
    sizes_text = message.text.strip()
    if sizes_text == "0":
        sizes = []
    else:
        sizes = [s.strip() for s in sizes_text.split(',')]
    
    await state.update_data(sizes=json.dumps(sizes))
    await message.answer("📦 Omborda nechta mavjud:")
    await AddProduct.stock.set()

@dp.message_handler(state=AddProduct.stock)
async def add_product_stock(message: types.Message, state: FSMContext):
    try:
        stock = int(message.text)
        await state.update_data(stock=stock)
        await message.answer("📸 Mahsulot rasmini yuboring (yoki 0 - rasm yo'q):")
        await AddProduct.image.set()
    except:
        await message.answer("❌ Noto'g'ri format! Butun son kiriting:")

@dp.message_handler(state=AddProduct.image, content_types=['photo', 'text'])
async def add_product_image(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    if message.content_type == 'photo':
        image_id = message.photo[-1].file_id
    else:
        image_id = None
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''INSERT INTO products (name, description, price, old_price, category_id, sizes, stock, image_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['name'], data['description'], data['price'], data.get('old_price'),
               data['category_id'], data['sizes'], data['stock'], image_id))
    conn.commit()
    conn.close()
    
    await state.finish()
    
    discount_text = ""
    if data.get('old_price') and data['old_price'] > data['price']:
        discount = int((1 - data['price']/data['old_price']) * 100)
        discount_text = f"\n🔥 Chegirma: {discount}%"
    
    await message.answer(
        f"✅ Mahsulot qo'shildi!\n\n"
        f"📦 {data['name']}\n"
        f"💰 {format_price(data['price'])} {get_setting('currency')}{discount_text}",
        reply_markup=get_admin_keyboard()
    )

# Edit product
@dp.callback_query_handler(lambda c: c.data.startswith('editprod_'))
async def edit_product_menu(callback: types.CallbackQuery):
    prod_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT name, description, price, old_price, stock, is_active, views, 
                        (SELECT COUNT(*) FROM reviews WHERE product_id = p.id) as review_count,
                        (SELECT AVG(rating) FROM reviews WHERE product_id = p.id) as avg_rating
                 FROM products p WHERE id = ?''', (prod_id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        await callback.answer("❌ Mahsulot topilmadi")
        return
    
    name, desc, price, old_price, stock, is_active, views, review_count, avg_rating = product
    status = "✅ Faol" if is_active else "❌ Nofaol"
    
    text = f"📦 <b>{name}</b>\n\n"
    text += f"📝 {desc}\n\n"
    text += f"💰 Narx: {format_price(price)} {get_setting('currency')}\n"
    if old_price:
        text += f"🔥 Eski narx: {format_price(old_price)} {get_setting('currency')}\n"
    text += f"📦 Omborda: {stock}\n"
    text += f"📊 Holat: {status}\n"
    text += f"👁 Ko'rishlar: {views}\n"
    if review_count:
        text += f"⭐ Reyting: {avg_rating:.1f}/5 ({review_count} sharh)\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    toggle_text = "❌ Faolsizlantirish" if is_active else "✅ Faollashtirish"
    markup.add(
        InlineKeyboardButton(toggle_text, callback_data=f"toggleprod_{prod_id}"),
        InlineKeyboardButton("📊 Statistika", callback_data=f"prodstats_{prod_id}")
    )
    markup.add(
        InlineKeyboardButton("✏️ Narx", callback_data=f"editprodprice_{prod_id}"),
        InlineKeyboardButton("📦 Ombor", callback_data=f"editprodstock_{prod_id}")
    )
    markup.row(InlineKeyboardButton("🗑 O'chirish", callback_data=f"delprod_{prod_id}"))
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_products_admin"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Toggle product status
@dp.callback_query_handler(lambda c: c.data.startswith('toggleprod_'))
async def toggle_product(callback: types.CallbackQuery):
    prod_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE products SET is_active = NOT is_active WHERE id = ?', (prod_id,))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Holat o'zgartirildi")
    await edit_product_menu(callback)

# Delete product
@dp.callback_query_handler(lambda c: c.data.startswith('delprod_'))
async def delete_product(callback: types.CallbackQuery):
    prod_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id = ?', (prod_id,))
    c.execute('DELETE FROM cart WHERE product_id = ?', (prod_id,))
    c.execute('DELETE FROM wishlist WHERE product_id = ?', (prod_id,))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Mahsulot o'chirildi!")
    await callback.message.delete()
    #manbaa @krv_coder

# Orders management
@dp.message_handler(lambda m: m.text == "🛍 Buyurtmalar" and is_admin(m.from_user.id))
async def admin_orders(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT o.order_number, u.full_name, o.total_price, o.status, o.created_at
                 FROM orders o
                 JOIN users u ON o.user_id = u.user_id
                 ORDER BY o.created_at DESC
                 LIMIT 20''')
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        await message.answer("📦 Buyurtmalar yo'q")
        return
    
    text = "🛍 <b>Buyurtmalar</b>\n\n"
    
    status_emoji = {
        'pending': '⏳',
        'confirmed': '✅',
        'cancelled': '❌',
        'delivered': '🚚'
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for order_num, full_name, total, status, created in orders:
        emoji = status_emoji.get(status, '❓')
        text += f"{emoji} {order_num} - {full_name}\n"
        text += f"   💰 {format_price(total)} {get_setting('currency')} | {created[:16]}\n\n"
        
        markup.add(InlineKeyboardButton(
            f"{emoji} {order_num} - {full_name}",
            callback_data=f"admin_order_{order_num}"
        ))
    
    # Filter buttons
    markup.row(
        InlineKeyboardButton("⏳ Kutilmoqda", callback_data="filter_pending"),
        InlineKeyboardButton("✅ Tasdiqlangan", callback_data="filter_confirmed")
    )
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Filter orders
@dp.callback_query_handler(lambda c: c.data.startswith('filter_'))
async def filter_orders(callback: types.CallbackQuery):
    status = callback.data.split('_')[1]
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT o.order_number, u.full_name, o.total_price, o.status, o.created_at
                 FROM orders o
                 JOIN users u ON o.user_id = u.user_id
                 WHERE o.status = ?
                 ORDER BY o.created_at DESC
                 LIMIT 20''', (status,))
    orders = c.fetchall()
    conn.close()
    
    if not orders:
        await callback.answer(f"Bu holatda buyurtmalar yo'q")
        return
    
    status_emoji = {
        'pending': '⏳',
        'confirmed': '✅',
        'cancelled': '❌',
        'delivered': '🚚'
    }
    
    status_text = {
        'pending': 'Kutilmoqda',
        'confirmed': 'Tasdiqlangan',
        'cancelled': 'Bekor qilingan',
        'delivered': 'Yetkazilgan'
    }
    
    text = f"🛍 <b>Buyurtmalar: {status_text.get(status)}</b>\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for order_num, full_name, total, status, created in orders:
        emoji = status_emoji.get(status, '❓')
        text += f"{emoji} {order_num} - {full_name}\n"
        text += f"   💰 {format_price(total)} {get_setting('currency')} | {created[:16]}\n\n"
        
        markup.add(InlineKeyboardButton(
            f"{emoji} {order_num}",
            callback_data=f"admin_order_{order_num}"
        ))
    
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_orders_admin"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Admin order details
@dp.callback_query_handler(lambda c: c.data.startswith('admin_order_'))
async def admin_order_details(callback: types.CallbackQuery):
    order_number = callback.data.split('_', 2)[2]
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT o.items, o.total_price, o.status, o.created_at, o.payment_check,
                        u.full_name, u.phone, u.user_id, o.delivery_address, o.delivery_method,
                        o.payment_method, o.notes
                 FROM orders o
                 JOIN users u ON o.user_id = u.user_id
                 WHERE o.order_number = ?''', (order_number,))
    order = c.fetchone()
    conn.close()
    
    if not order:
        await callback.answer("❌ Buyurtma topilmadi")
        return
    
    items_json, total, status, created, check_id, full_name, phone, user_id, address, delivery, payment, notes = order
    items = json.loads(items_json)
    
    status_text = {
        'pending': '⏳ Kutilmoqda',
        'confirmed': '✅ Tasdiqlangan',
        'cancelled': '❌ Bekor qilingan',
        'delivered': '🚚 Yetkazilgan'
    }
    
    text = f"📋 <b>Buyurtma #{order_number}</b>\n\n"
    text += f"👤 Mijoz: {full_name}\n"
    text += f"📱 Telefon: {phone}\n"
    text += f"📅 Sana: {created[:16]}\n"
    text += f"📊 Holat: {status_text.get(status, status)}\n"
    text += f"🚚 Yetkazish: {delivery}\n"
    if delivery == 'courier':
        text += f"📍 Manzil: {address}\n"
    text += f"💳 To'lov: {payment}\n"
    if notes:
        text += f"📝 Izoh: {notes}\n"
    text += "\n<b>Mahsulotlar:</b>\n"
    
    for item in items:
        size_text = f" ({item['size']})" if item.get('size') else ""
        text += f"• {item['name']}{size_text}\n"
        text += f"  {item['quantity']} x {format_price(item['price'])} = {format_price(item['price'] * item['quantity'])} {get_setting('currency')}\n"
    
    text += f"\n💰 <b>Jami: {format_price(total)} {get_setting('currency')}</b>"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    if status == 'pending':
        markup.add(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_order_{order_number}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_order_{order_number}")
        )
    elif status == 'confirmed':
        markup.row(InlineKeyboardButton("🚚 Yetkazildi", callback_data=f"deliver_order_{order_number}"))
    
    markup.row(InlineKeyboardButton("💬 Mijoz bilan chat", callback_data=f"chat_{user_id}"))
    
    if check_id:
        markup.row(InlineKeyboardButton("📸 Chekni ko'rish", callback_data=f"viewcheck_{check_id}"))
    
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_admin_orders"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# View check
@dp.callback_query_handler(lambda c: c.data.startswith('viewcheck_'))
async def view_check(callback: types.CallbackQuery):
    check_id = callback.data.split('_')[1]
    
    try:
        await bot.send_photo(callback.from_user.id, check_id, caption="📸 To'lov cheki")
    except:
        await callback.answer("❌ Chekni ko'rsatib bo'lmadi")

# Users management
@dp.message_handler(lambda m: m.text == "👥 Foydalanuvchilar" and is_admin(m.from_user.id))
async def manage_users(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM users WHERE is_blocked = 1')
    blocked = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM users WHERE DATE(registered_at) = DATE("now")')
    today = c.fetchone()[0]
    
    c.execute('''SELECT user_id, full_name, phone, registered_at 
                 FROM users 
                 ORDER BY registered_at DESC 
                 LIMIT 10''')
    recent_users = c.fetchall()
    conn.close()
    
    text = f"👥 <b>Foydalanuvchilar</b>\n\n"
    text += f"📊 Jami: {total}\n"
    text += f"🚫 Bloklangan: {blocked}\n"
    text += f"🆕 Bugun: {today}\n\n"
    text += "<b>Oxirgi foydalanuvchilar:</b>\n\n"
    #manbaa @krv_coder
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for user_id, full_name, phone, registered in recent_users:
        text += f"👤 {full_name} - {phone}\n   📅 {registered[:10]}\n"
        markup.add(InlineKeyboardButton(
            f"👤 {full_name}",
            callback_data=f"userinfo_{user_id}"
        ))
    
    markup.row(InlineKeyboardButton("🔍 Qidiruv", switch_inline_query_current_chat="user:"))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# User info
@dp.callback_query_handler(lambda c: c.data.startswith('userinfo_'))
async def user_info(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT full_name, phone, balance, registered_at, is_blocked FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    
    c.execute('SELECT COUNT(*), SUM(total_price) FROM orders WHERE user_id = ?', (user_id,))
    orders_count, total_spent = c.fetchone()
    total_spent = total_spent or 0
    
    c.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
    referrals = c.fetchone()[0]
    
    conn.close()
    
    if not user:
        await callback.answer("❌ Foydalanuvchi topilmadi")
        return
    
    full_name, phone, balance, registered, is_blocked = user
    status = "🚫 Bloklangan" if is_blocked else "✅ Faol"
    
    text = f"👤 <b>{full_name}</b>\n\n"
    text += f"🆔 ID: <code>{user_id}</code>\n"
    text += f"📱 Telefon: {phone}\n"
    text += f"💰 Balans: {format_price(balance)} {get_setting('currency')}\n"
    text += f"📅 Ro'yxatdan: {registered[:10]}\n"
    text += f"📊 Holat: {status}\n\n"
    text += f"📦 Buyurtmalar: {orders_count}\n"
    text += f"💸 Xarajat: {format_price(total_spent)} {get_setting('currency')}\n"
    text += f"👥 Referallar: {referrals}\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    block_text = "✅ Blokdan chiqarish" if is_blocked else "🚫 Bloklash"
    markup.add(
        InlineKeyboardButton(block_text, callback_data=f"toggleblock_{user_id}"),
        InlineKeyboardButton("💬 Chat", callback_data=f"chat_{user_id}")
    )
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_users"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Toggle user block
@dp.callback_query_handler(lambda c: c.data.startswith('toggleblock_'))
async def toggle_user_block(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE users SET is_blocked = NOT is_blocked WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Holat o'zgartirildi")
    await user_info(callback)

# Promocodes management
@dp.message_handler(lambda m: m.text == "🎁 Promokodlar" and is_admin(m.from_user.id))
async def manage_promocodes(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT code, discount_percent, discount_amount, max_uses, used_count, is_active
                 FROM promocodes
                 ORDER BY created_at DESC''')
    promocodes = c.fetchall()
    conn.close()
    
    text = "🎁 <b>Promokodlar</b>\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    if promocodes:
        for code, percent, amount, max_uses, used, is_active in promocodes:
            status = "✅" if is_active else "❌"
            discount = f"{percent}%" if percent else f"{format_price(amount)} {get_setting('currency')}"
            usage = f"{used}/{max_uses if max_uses else '∞'}"
            text += f"{status} <code>{code}</code> - {discount} ({usage})\n"
            markup.add(InlineKeyboardButton(
                f"{status} {code} - {discount}",
                callback_data=f"editpromo_{code}"
            ))
    else:
        text += "Promokodlar yo'q\n"
    
    markup.add(InlineKeyboardButton("➕ Yangi promokod", callback_data="add_promocode"))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Add promocode
@dp.callback_query_handler(lambda c: c.data == "add_promocode")
async def add_promocode_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎁 <b>Yangi promokod</b>\n\n"
        "Promokod kodini kiriting (masalan: SALE20):",
        parse_mode='HTML'
    )
    await AddPromocode.code.set()

@dp.message_handler(state=AddPromocode.code)
async def add_promo_code(message: types.Message, state: FSMContext):
    code = message.text.upper()
    
    # Check if code exists
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT id FROM promocodes WHERE code = ?', (code,))
    if c.fetchone():
        await message.answer("❌ Bu kod allaqachon mavjud! Boshqa kod kiriting:")
        conn.close()
        return
    conn.close()
    
    await state.update_data(code=code)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Foiz", callback_data="discount_percent"),
        InlineKeyboardButton("💰 Summa", callback_data="discount_amount")
    )
    
    await message.answer(
        "📊 Chegirma turini tanlang:",
        reply_markup=markup
    )
    await AddPromocode.discount_type.set()

@dp.callback_query_handler(lambda c: c.data.startswith('discount_'), state=AddPromocode.discount_type)
async def add_promo_type(callback: types.CallbackQuery, state: FSMContext):
    discount_type = callback.data.split('_')[1]
    await state.update_data(discount_type=discount_type)
    
    if discount_type == 'percent':
        await callback.message.edit_text("📊 Chegirma foizini kiriting (1-99):")
    else:
        await callback.message.edit_text(f"💰 Chegirma summasini kiriting ({get_setting('currency')}):")
    
    await AddPromocode.discount_value.set()

@dp.message_handler(state=AddPromocode.discount_value)
async def add_promo_value(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        data = await state.get_data()
        
        if data['discount_type'] == 'percent' and (value < 1 or value > 99):
            await message.answer("❌ Foiz 1 dan 99 gacha bo'lishi kerak!")
            return
        
        await state.update_data(discount_value=value)
        await message.answer(
            "🔢 Maksimal foydalanish soni:\n"
            "(0 - cheksiz)"
        )
        await AddPromocode.max_uses.set()
    except:
        await message.answer("❌ Noto'g'ri format! Raqam kiriting:")
    #manbaa @krv_coder

@dp.message_handler(state=AddPromocode.max_uses)
async def add_promo_max_uses(message: types.Message, state: FSMContext):
    try:
        max_uses = int(message.text)
        if max_uses < 0:
            await message.answer("❌ Manfiy son kiritib bo'lmaydi!")
            return
        
        await state.update_data(max_uses=max_uses if max_uses > 0 else None)
        await message.answer("📅 Necha kun amal qiladi:")
        await AddPromocode.valid_days.set()
    except:
        await message.answer("❌ Noto'g'ri format! Butun son kiriting:")

@dp.message_handler(state=AddPromocode.valid_days)
async def add_promo_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days < 1:
            await message.answer("❌ Kamida 1 kun bo'lishi kerak!")
            return
        
        data = await state.get_data()
        
        conn = sqlite3.connect('shop.db')
        c = conn.cursor()
        
        if data['discount_type'] == 'percent':
            c.execute('''INSERT INTO promocodes (code, discount_percent, max_uses, valid_from, valid_until)
                         VALUES (?, ?, ?, datetime('now'), datetime('now', '+' || ? || ' days'))''',
                      (data['code'], data['discount_value'], data['max_uses'], days))
        else:
            c.execute('''INSERT INTO promocodes (code, discount_amount, max_uses, valid_from, valid_until)
                         VALUES (?, ?, ?, datetime('now'), datetime('now', '+' || ? || ' days'))''',
                      (data['code'], data['discount_value'], data['max_uses'], days))
        
        conn.commit()
        conn.close()
        
        await state.finish()
        
        discount = f"{int(data['discount_value'])}%" if data['discount_type'] == 'percent' else f"{format_price(data['discount_value'])} {get_setting('currency')}"
        
        await message.answer(
            f"✅ <b>Promokod yaratildi!</b>\n\n"
            f"🎁 Kod: <code>{data['code']}</code>\n"
            f"📊 Chegirma: {discount}\n"
            f"🔢 Limit: {data['max_uses'] or 'Cheksiz'}\n"
            f"📅 Amal qilish: {days} kun",
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
    except:
        await message.answer("❌ Noto'g'ri format! Butun son kiriting:")

# Reviews management
@dp.message_handler(lambda m: m.text == "⭐ Sharhlar" and is_admin(m.from_user.id))
async def manage_reviews(message: types.Message):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('''SELECT r.id, p.name, u.full_name, r.rating, r.comment, r.created_at
                 FROM reviews r
                 JOIN products p ON r.product_id = p.id
                 JOIN users u ON r.user_id = u.user_id
                 ORDER BY r.created_at DESC
                 LIMIT 20''')
    reviews = c.fetchall()
    
    c.execute('SELECT COUNT(*), AVG(rating) FROM reviews')
    total, avg_rating = c.fetchone()
    
    conn.close()
    
    text = f"⭐ <b>Sharhlar</b>\n\n"
    text += f"📊 Jami: {total}\n"
    text += f"⭐ O'rtacha: {avg_rating:.1f}/5\n\n"
    
    if reviews:
        for review_id, prod_name, user_name, rating, comment, created in reviews:
            stars = "⭐" * rating
            text += f"{stars} {prod_name}\n"
            text += f"👤 {user_name} | {created[:10]}\n"
            if comment:
                text += f"💬 {comment[:50]}...\n" if len(comment) > 50 else f"💬 {comment}\n"
            text += "\n"
    else:
        text += "Sharhlar yo'q"
    
    await message.answer(text, parse_mode='HTML')

# Settings
@dp.message_handler(lambda m: m.text == "⚙️ Sozlamalar" and is_admin(m.from_user.id))
async def settings_menu(message: types.Message):
    card_number = get_setting('card_number')
    card_owner = get_setting('card_owner')
    ref_bonus = get_setting('referral_bonus')
    delivery_price = get_setting('delivery_price')
    free_delivery = get_setting('free_delivery_from')
    
    text = f"⚙️ <b>Sozlamalar</b>\n\n"
    text += f"💳 Karta: {card_number}\n"
    text += f"👤 Egasi: {card_owner}\n"
    text += f"🎁 Referal bonus: {format_price(int(ref_bonus))} {get_setting('currency')}\n"
    text += f"🚚 Yetkazish: {format_price(int(delivery_price))} {get_setting('currency')}\n"
    text += f"🆓 Bepul yetkazish: {format_price(int(free_delivery))} {get_setting('currency')} dan\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📢 Majburiy obuna", callback_data="manage_channels"),
        InlineKeyboardButton("👨‍💼 Adminlar", callback_data="manage_admins"),
        InlineKeyboardButton("💳 Karta sozlamalari", callback_data="card_settings"),
        InlineKeyboardButton("🚚 Yetkazish sozlamalari", callback_data="delivery_settings"),
        InlineKeyboardButton("🎁 Referal sozlamalari", callback_data="referral_settings")
    )
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Card settings
@dp.callback_query_handler(lambda c: c.data == "card_settings")
async def card_settings(callback: types.CallbackQuery, state: FSMContext):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("💳 Karta raqami", callback_data="edit_card_number"),
        InlineKeyboardButton("👤 Karta egasi", callback_data="edit_card_owner"),
        InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_settings")
    )
    
    await callback.message.edit_text(
        "💳 <b>Karta sozlamalari</b>\n\n"
        "O'zgartirish uchun tanlang:",
        reply_markup=markup,
        parse_mode='HTML'
    )

@dp.callback_query_handler(lambda c: c.data.startswith('edit_card_'))
async def edit_card_setting(callback: types.CallbackQuery, state: FSMContext):
    setting = callback.data.split('_', 2)[2]
    await state.update_data(setting_key=f"card_{setting}")
    
    if setting == 'number':
        text = "💳 Yangi karta raqamini kiriting:"
    else:
        text = "👤 Yangi karta egasi ismini kiriting:"
    
    await callback.message.edit_text(text)
    await EditSettings.value.set()

@dp.message_handler(state=EditSettings.value)
async def save_setting(message: types.Message, state: FSMContext):
    data = await state.get_data()
    key = data['setting_key']
    value = message.text
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE settings SET value = ? WHERE key = ?', (value, key))
    conn.commit()
    conn.close()
    
    await state.finish()
    await message.answer(
        f"✅ Sozlama yangilandi!\n\n{key}: {value}",
        reply_markup=get_admin_keyboard()
    )

# Manage channels
@dp.callback_query_handler(lambda c: c.data == "manage_channels")
async def manage_channels(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT id, channel_name, channel_username, is_active FROM channels ORDER BY id')
    channels = c.fetchall()
    conn.close()
    
    text = "📢 <b>Majburiy obuna kanallari</b>\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    if channels:
        for ch_id, name, username, is_active in channels:
            status = "✅" if is_active else "❌"
            text += f"{status} {name} (@{username})\n"
            markup.add(InlineKeyboardButton(
                f"{status} {name}",
                callback_data=f"editchan_{ch_id}"
            ))
    else:
        text += "Kanallar yo'q\n"
    
    markup.add(InlineKeyboardButton("➕ Kanal qo'shish", callback_data="add_channel"))
    markup.add(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_settings"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Edit channel
@dp.callback_query_handler(lambda c: c.data.startswith('editchan_'))
async def edit_channel(callback: types.CallbackQuery):
    ch_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT channel_name, channel_username, is_active FROM channels WHERE id = ?', (ch_id,))
    channel = c.fetchone()
    conn.close()
    
    if not channel:
        await callback.answer("❌ Kanal topilmadi")
        return
    
    name, username, is_active = channel
    status = "✅ Faol" if is_active else "❌ Nofaol"
    
    text = f"📢 <b>{name}</b>\n\n"
    text += f"🔗 @{username}\n"
    text += f"📊 Holat: {status}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    toggle_text = "❌ Faolsizlantirish" if is_active else "✅ Faollashtirish"
    markup.add(
        InlineKeyboardButton(toggle_text, callback_data=f"togglechan_{ch_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"delchan_{ch_id}")
    )
    markup.row(InlineKeyboardButton("◀️ Orqaga", callback_data="manage_channels"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Toggle channel
@dp.callback_query_handler(lambda c: c.data.startswith('togglechan_'))
async def toggle_channel(callback: types.CallbackQuery):
    ch_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('UPDATE channels SET is_active = NOT is_active WHERE id = ?', (ch_id,))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Holat o'zgartirildi")
    await edit_channel(callback)

# Add channel
@dp.callback_query_handler(lambda c: c.data == "add_channel")
async def add_channel_start(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📢 <b>Yangi kanal qo'shish</b>\n\n"
        "Kanal ID sini kiriting (masalan: -1001234567890)\n"
        "yoki username kiriting (@channel)\n\n"
        "Yoki /cancel",
        parse_mode='HTML'
    )
    await AddChannel.channel_id.set()

@dp.message_handler(state=AddChannel.channel_id)
async def add_channel_id(message: types.Message, state: FSMContext):
    try:
        channel_id = message.text.strip()
        # Test channel
        chat = await bot.get_chat(channel_id)
        
        conn = sqlite3.connect('shop.db')
        c = conn.cursor()
        c.execute('INSERT INTO channels (channel_id, channel_username, channel_name) VALUES (?, ?, ?)',
                  (str(chat.id), chat.username or "", chat.title))
        conn.commit()
        conn.close()
        
        await state.finish()
        await message.answer(
            f"✅ Kanal qo'shildi!\n\n"
            f"📢 {chat.title}\n"
            f"🔗 @{chat.username or 'Private'}",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        await message.answer(
            f"❌ Xatolik: {str(e)}\n\n"
            "Botni kanalga admin qiling va qaytadan urinib ko'ring!"
        )
        await state.finish()

# Delete channel
@dp.callback_query_handler(lambda c: c.data.startswith('delchan_'))
async def delete_channel(callback: types.CallbackQuery):
    ch_id = int(callback.data.split('_')[1])
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('DELETE FROM channels WHERE id = ?', (ch_id,))
    conn.commit()
    conn.close()
    
    await callback.answer("✅ Kanal o'chirildi!")
    await manage_channels(callback)

# Manage admins
@dp.callback_query_handler(lambda c: c.data == "manage_admins")
async def manage_admins_menu(callback: types.CallbackQuery):
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM admins ORDER BY added_at')
    admins = c.fetchall()
    conn.close()
    
    text = "👨‍💼 <b>Adminlar</b>\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for (admin_id,) in admins:
        try:
            user = await bot.get_chat(admin_id)
            name = user.full_name or user.username or str(admin_id)
            text += f"• {name} (<code>{admin_id}</code>)\n"
            if admin_id != ADMIN_ID:
                markup.add(InlineKeyboardButton(f"➖ {name}", callback_data=f"deladmin_{admin_id}"))
        except:
            text += f"• User {admin_id}\n"
    
    markup.add(InlineKeyboardButton("➕ Admin qo'shish", switch_inline_query="addadmin:"))
    markup.add(InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_settings"))
    
    await callback.message.edit_text(text, reply_markup=markup, parse_mode='HTML')

# Info
@dp.message_handler(lambda m: m.text == "ℹ️ Ma'lumot")
async def info_handler(message: types.Message):
    text = "ℹ️ <b>Online Do'kon</b>\n\n"
    text += "🛍 Eng sifatli mahsulotlar\n"
    text += "🚚 Tez yetkazib berish\n"
    text += "💳 Qulay to'lov\n"
    text += "💎 Referal tizimi\n"
    text += "⭐ Ishonchli xizmat\n\n"
    text += f"📞 Telefon: {get_setting('shop_phone')}\n"
    text += f"📧 Email: {get_setting('shop_email')}\n"
    text += f"🏢 Manzil: {get_setting('shop_address')}\n"
    text += f"⏰ Ish vaqti: {get_setting('work_hours')}\n\n"
    text += "📞 Yordam kerakmi? /start"
    
    await message.answer(text, parse_mode='HTML')

# Contact
@dp.message_handler(lambda m: m.text == "☎️ Bog'lanish")
async def contact_handler(message: types.Message):
    text = "☎️ <b>Biz bilan bog'lanish</b>\n\n"
    text += f"📞 Telefon: {get_setting('shop_phone')}\n"
    text += f"📧 Email: {get_setting('shop_email')}\n"
    text += f"🏢 Manzil: {get_setting('shop_address')}\n\n"
    text += f"⏰ Ish vaqti: {get_setting('work_hours')}\n\n"
    text += "Sizning savollaringiz bizga muhim!"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📞 Telefon qilish", url=f"tel:{get_setting('shop_phone').replace(' ', '')}"))
    
    await message.answer(text, reply_markup=markup, parse_mode='HTML')

# Back buttons
@dp.callback_query_handler(lambda c: c.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery):
    await show_products(callback.message)

@dp.callback_query_handler(lambda c: c.data == "back_to_categories_admin")
async def back_to_categories_admin(callback: types.CallbackQuery):
    await callback.message.delete()

@dp.callback_query_handler(lambda c: c.data == "back_to_products_admin")
async def back_to_products_admin(callback: types.CallbackQuery):
    await callback.message.delete()

@dp.callback_query_handler(lambda c: c.data == "back_to_orders")
async def back_to_orders(callback: types.CallbackQuery):
    await my_orders(callback.message)

@dp.callback_query_handler(lambda c: c.data == "back_to_admin_orders")
async def back_to_admin_orders(callback: types.CallbackQuery):
    await callback.message.delete()

@dp.callback_query_handler(lambda c: c.data == "back_to_settings")
async def back_to_settings(callback: types.CallbackQuery):
    await callback.message.delete()

@dp.callback_query_handler(lambda c: c.data == "back_to_users")
async def back_to_users(callback: types.CallbackQuery):
    await callback.message.delete()

# Back to main menu
@dp.message_handler(lambda m: m.text == "🔙 Orqaga" and is_admin(m.from_user.id))
async def back_to_main(message: types.Message):
    await message.answer(
        "🏠 Asosiy menyu",
        reply_markup=get_main_keyboard()
    )
    #manbaa @krv_coder

# Cancel handler
@dp.message_handler(commands=['cancel'], state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.finish()
    
    if is_admin(message.from_user.id):
        await message.answer("❌ Bekor qilindi", reply_markup=get_admin_keyboard())
    else:
        await message.answer("❌ Bekor qilindi", reply_markup=get_main_keyboard())

# Inline search for products
@dp.inline_handler()
async def inline_search(inline_query: types.InlineQuery):
    query = inline_query.query.strip().lower()
    
    conn = sqlite3.connect('shop.db')
    c = conn.cursor()
    
    if query:
        c.execute('''SELECT id, name, description, price, image_id 
                     FROM products 
                     WHERE (LOWER(name) LIKE ? OR LOWER(description) LIKE ?) 
                     AND is_active = 1 
                     LIMIT 10''', (f'%{query}%', f'%{query}%'))
    else:
        c.execute('''SELECT id, name, description, price, image_id 
                     FROM products 
                     WHERE is_active = 1 
                     ORDER BY views DESC 
                     LIMIT 10''')
    
    products = c.fetchall()
    conn.close()
    
    results = []
    for prod_id, name, desc, price, image_id in products:
        text = f"📦 {name}\n💰 {format_price(price)} {get_setting('currency')}\n\n{desc}"
        
        if image_id:
            result = types.InlineQueryResultPhoto(
                id=str(prod_id),
                photo_url=f"https://api.telegram.org/file/bot{API_TOKEN}/{image_id}",
                thumb_url=f"https://api.telegram.org/file/bot{API_TOKEN}/{image_id}",
                title=name,
                description=f"{format_price(price)} {get_setting('currency')}",
                caption=text,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🛒 Savatga", callback_data=f"addcart_{prod_id}_none")
                )
            )
        else:
            result = types.InlineQueryResultArticle(
                id=str(prod_id),
                title=name,
                description=f"{format_price(price)} {get_setting('currency')}",
                input_message_content=types.InputTextMessageContent(
                    message_text=text,
                    parse_mode='HTML'
                ),
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🛒 Ko'rish", callback_data=f"prod_{prod_id}")
                )
            )
        
        results.append(result)
    
    await bot.answer_inline_query(inline_query.id, results, cache_time=1)

# Handle all other messages
@dp.message_handler(state='*', content_types=types.ContentTypes.ANY)
async def unknown_message(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await cmd_start(message, None)
        return
    
    if await check_user_blocked(message.from_user.id):
        await message.answer("❌ Sizning akkauntingiz bloklangan.")
        return
    
    await message.answer(
        "❓ Buyruq noma'lum. /start ni bosing",
        reply_markup=get_main_keyboard() if not is_admin(message.from_user.id) else get_admin_keyboard()
    )

# Error handler
@dp.errors_handler()
async def errors_handler(update, exception):
    logging.exception(f'Update: {update} \n{exception}')
    return True

# Main
if __name__ == '__main__':
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import os

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Bot is running')

    def run_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), Handler)
        server.serve_forever()

    threading.Thread(target=run_server, daemon=True).start()

    print("=" * 50)
    print("🤖 Bot ishga tushdi!")
    print(f"👨‍💼 Admin ID: {ADMIN_ID}")
    print("📊 Database: shop.db")
    print("✅ Barcha funksiyalar faol")
    print("=" * 50)
    executor.start_polling(dp, skip_updates=True)

