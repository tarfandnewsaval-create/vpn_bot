import os
import re
import asyncio
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ===================== تنظیمات اصلی =====================
# توکن دیگه توی کد نوشته نمیشه! یه فایل به اسم .env کنار همین فایل بساز و این خط رو توش بنویس:
#   BOT_TOKEN=8398629457:AAG1-WJFsMvg3S9JCl14FncjlksSIgzIH88
# و پکیج python-dotenv رو نصب کن: pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError(
        "توکن بات پیدا نشد! متغیر محیطی BOT_TOKEN رو ست کن یا توی فایل .env بنویس."
    )

# آیدی عددی ادمین - این رو با دستور /myid از خود بات بگیر و اینجا جایگزین کن
ADMIN_ID = 8707644614

CARD_NUMBER = "6219861451146921"

SUPPORT_USERNAME = "@vpn_tarfand_admin"

# ===================== عضویت اجباری در کانال =====================
# توجه: قابلیت عضویت اجباری در کانال غیرفعاله (کانالی تنظیم نشده).
# اگه بعداً کانال ساختی، کافیه یوزرنیمش رو (با @) اینجا بذاری تا خودکار فعال بشه.
FORCE_JOIN_CHANNEL = None

# ===================== پیام‌های خودکار =====================
MORNING_MESSAGE = (
    "☀️ <b>صبح بخیر</b>\n\n"
    "روزت پر از انرژی و لبخند باشه 🌸\n"
    "ما همیشه اینجاییم، همیشه در کنارتون؛ هر وقت خواستی وصل بشی یا سوالی داشتی، "
    "فقط یه پیام تا ما فاصله داری 💙\n\n"
    "امیدواریم امروز روز خوبی برات باشه ✨"
)

PROMO_MESSAGE = (
    "🔥 <b>وقتشه سرعتت رو چند برابر کنی!</b>\n\n"
    "با پلن‌های ۱۰ تا ۲۰۰ گیگ، پرسرعت و پایدار، همین الان یه اشتراک تهیه کن "
    "و بدون محدودیت به دنیای آزاد وصل شو 🌐\n\n"
    "برای دیدن پلن‌ها و خرید همین الان /start رو بزن 🎁"
)

FORCE_JOIN_TEXT = (
    "🔒 <b>عضویت در کانال</b>\n\n"
    "برای استفاده از ربات، اول باید عضو کانال ما بشی:\n"
    f"👉 {FORCE_JOIN_CHANNEL}\n\n"
    "بعد از عضویت، روی دکمه‌ی زیر بزن تا ادامه بدیم ✅"
)

CONNECTION_GUIDE_TEXT = (
    "🛰 <b>راهنمای اتصال</b>\n\n"
    "۱. اپلیکیشن مناسب سیستم‌عاملت رو نصب کن (v2rayNG / Streisand / Hiddify و ...)\n"
    "۲. لینک/کانفیگی که برات ارسال شده رو کپی کن\n"
    "۳. داخل اپلیکیشن گزینه‌ی Import from Clipboard رو بزن\n"
    "۴. روی دکمه‌ی اتصال بزن و از سرویس لذت ببر ✅\n\n"
    "در صورت مشکل با پشتیبانی در ارتباط باش."
)

# هر خریدی که یک «زیرمجموعه» (کاربر دعوت‌شده) انجام بده، این مقدار به‌عنوان
# اعتبار کیف پول به دعوت‌کننده تعلق می‌گیره + یک امتیاز کوچک.
# اگه منظورت از "۲۵ تومان" عدد دیگه‌ایه، همینجا تغییرش بده.
REFERRAL_WALLET_REWARD = 25000
REFERRAL_POINT_REWARD = 1

# ===================== پلن‌های فروش =====================
PLANS = {
    "p10":     {"button": "10 گیگ یک ماهه",   "desc": "۶ کاربره | یک ماهه",  "price": 175000},
    "p20":     {"button": "20 گیگ یک ماهه",   "desc": "۶ کاربره | یک ماهه",  "price": 240000},
    "p30":     {"button": "30 گیگ یک ماهه",   "desc": "۶ کاربره | یک ماهه",  "price": 300000},
    "p40":     {"button": "40 گیگ یک ماهه",   "desc": "۶ کاربره | یک ماهه",  "price": 400000},
    "p50":     {"button": "50 گیگ یک ماهه",   "desc": "۶ کاربره | یک ماهه",  "price": 450000},
    "p100_1m": {"button": "100 گیگ یک ماهه",  "desc": "۶ کاربره | یک ماهه",  "price": 650000},
    "p100_3m": {"button": "100 گیگ سه ماهه",  "desc": "۶ کاربره | سه ماهه", "price": 685000},
    "p200_3m": {"button": "200 گیگ سه ماهه",  "desc": "۶ کاربره | سه ماهه", "price": 1100000},
}

MODE_TITLE = {"buy": "🎁 خرید اشتراک", "renew": "🔄 تمدید اشتراک"}

# ===================== حافظه‌ی موقت (در RAM) =====================
# {user_id: {"referred_by": int|None, "wallet": int, "points": int,
#            "ref_count": int, "orders": [ {...} ]}}
users = {}

# {user_id: {"mode": "buy"|"renew"|"wallet", "plan": key|None, "name": str|None,
#            "amount": int|None, "wallet_used": int, "stage": str}}
pending_orders = {}

# {admin_id: {"user_id": int, "mode": "buy"|"renew"|"wallet", "plan": key|None,
#             "amount": int|None}}
waiting_for_config = {}

# {admin_id: {"stage": "awaiting_text"|"awaiting_confirm", "target": "all"|"buyers"|"non_buyers",
#             "text": str|None}}
broadcast_state = {}

# {admin_id: {"stage": "awaiting_target"|"awaiting_text"|"awaiting_confirm",
#             "target_id": int|None, "text": str|None}}
direct_msg_state = {}


async def is_member_of_channel(user_id, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """بررسی می‌کنه کاربر عضو کانال اجباری هست یا نه."""
    if not FORCE_JOIN_CHANNEL:
        return True
    try:
        member = await context.bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        # اگه ربات ادمین کانال نباشه یا کانال درست تنظیم نشده باشه، جلوی کاربر رو نمی‌گیریم
        return True


def force_join_keyboard():
    channel_link = f"https://t.me/{FORCE_JOIN_CHANNEL.lstrip('@')}"
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال", url=channel_link)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "referred_by": None,
            "wallet": 0,
            "points": 0,
            "ref_count": 0,
            "purchase_count": 0,
            "username": None,
        }
    return users[user_id]


def find_user_by_username(query_text):
    """یوزرنیم (با یا بدون @) رو بین کاربرای شناخته‌شده‌ی بات پیدا می‌کنه."""
    query_text = query_text.strip().lstrip("@").lower()
    if not query_text:
        return None
    for uid, u in users.items():
        uname = u.get("username")
        if uname and uname.lower() == query_text:
            return uid
    return None


# ===================== کیبوردها =====================
def main_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🔄 تمدید اشتراک", callback_data="menu_renew"),
         InlineKeyboardButton("🎁 خرید اشتراک", callback_data="menu_buy")],
        [InlineKeyboardButton("👥 زیر مجموعه گیری", callback_data="menu_referral"),
         InlineKeyboardButton("💰 کیف پول + شارژ", callback_data="menu_wallet")],
        [InlineKeyboardButton("🧑 ارتباط با پشتیبانی", callback_data="menu_support"),
         InlineKeyboardButton("🛰 راهنمای اتصال", callback_data="menu_guide")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📊 آمار ربات (ادمین)", callback_data="menu_stats")])
    return InlineKeyboardMarkup(keyboard)


def back_button(target="menu_main", label="🔙 بازگشت"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=target)]])


def plans_keyboard(mode):
    keyboard = []
    for key, plan in PLANS.items():
        label = f"{plan['button']} - {plan['price']:,} تومان"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"plan_{mode}_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")])
    return InlineKeyboardMarkup(keyboard)


def wallet_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_topup")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ===================== کیبورد پایین صفحه (همیشه کنار جعبه‌ی نوشتن) =====================
BTN_BUY = "🎁 خرید کانفیگ"
BTN_RENEW = "🔄 تمدید اشتراک"
BTN_WALLET = "💰 کیف پول"
BTN_REFERRAL = "👥 زیرمجموعه‌گیری"
BTN_SUPPORT = "🧑 پشتیبانی"
BTN_GUIDE = "🛰 راهنمای اتصال"
BTN_STATS = "📊 آمار ربات (ادمین)"
BTN_BROADCAST = "📢 ارسال پیام همگانی"
BTN_DIRECT_MSG = "✉️ پیام به کاربر خاص"


def reply_keyboard_markup(user_id):
    rows = [
        [BTN_BUY, BTN_RENEW],
        [BTN_WALLET, BTN_REFERRAL],
        [BTN_SUPPORT, BTN_GUIDE],
    ]
    if user_id == ADMIN_ID:
        rows.append([BTN_STATS, BTN_BROADCAST])
        rows.append([BTN_DIRECT_MSG])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


# ===================== روتر دکمه‌های کیبورد پایین =====================
async def reply_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    u = get_user(user.id)

    if text == BTN_BUY:
        pending_orders.pop(user.id, None)
        await update.message.reply_text(
            "🎁 لطفاً یکی از پلن‌های زیر رو برای خرید انتخاب کن 👇",
            reply_markup=plans_keyboard("buy")
        )

    elif text == BTN_RENEW:
        pending_orders.pop(user.id, None)
        await update.message.reply_text(
            "🔄 لطفاً پلنی که می‌خوای تمدید کنی رو انتخاب کن 👇",
            reply_markup=plans_keyboard("renew")
        )

    elif text == BTN_WALLET:
        await update.message.reply_text(
            build_wallet_text(u), parse_mode="HTML", reply_markup=wallet_menu_keyboard()
        )

    elif text == BTN_REFERRAL:
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start=REF{user.id}"
        await update.message.reply_text(
            build_referral_text(u, invite_link), parse_mode="HTML", reply_markup=back_button()
        )

    elif text == BTN_SUPPORT:
        await update.message.reply_text(SUPPORT_TEXT, parse_mode="HTML", reply_markup=back_button())

    elif text == BTN_GUIDE:
        await update.message.reply_text(
            CONNECTION_GUIDE_TEXT, parse_mode="HTML", reply_markup=back_button()
        )

    elif text == BTN_STATS:
        if user.id != ADMIN_ID:
            await update.message.reply_text("این بخش فقط برای ادمینه.")
            return
        await update.message.reply_text(build_stats_text(), parse_mode="HTML", reply_markup=back_button())

    elif text == BTN_BROADCAST:
        if user.id != ADMIN_ID:
            await update.message.reply_text("این بخش فقط برای ادمینه.")
            return
        broadcast_state[user.id] = {"stage": "awaiting_target"}
        await update.message.reply_text(
            "📢 <b>ارسال پیام همگانی</b>\n\nپیامت رو برای کدوم گروه بفرستم؟",
            parse_mode="HTML",
            reply_markup=broadcast_target_keyboard()
        )

    elif text == BTN_DIRECT_MSG:
        if user.id != ADMIN_ID:
            await update.message.reply_text("این بخش فقط برای ادمینه.")
            return
        direct_msg_state[user.id] = {"stage": "awaiting_target"}
        await update.message.reply_text(
            "✉️ <b>پیام به یک کاربر خاص</b>\n\n"
            "یوزرنیم کاربر رو بفرست (با یا بدون @) یا آیدی عددیش رو (اگه داری).\n"
            "⚠️ توجه: فقط کاربرایی که حداقل یک‌بار ربات رو /start کرده باشن قابل پیدا شدن هستن.",
            parse_mode="HTML"
        )


# ===================== دستورات =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)
    u["username"] = user.username

    if context.args:
        payload = context.args[0]
        if payload.startswith("REF"):
            try:
                referrer_id = int(payload[3:])
            except ValueError:
                referrer_id = None
            if referrer_id and referrer_id != user.id and u["referred_by"] is None and referrer_id in users:
                u["referred_by"] = referrer_id
                users[referrer_id]["ref_count"] += 1

    if not await is_member_of_channel(user.id, context):
        await update.message.reply_text(
            FORCE_JOIN_TEXT, parse_mode="HTML", reply_markup=force_join_keyboard()
        )
        return

    await update.message.reply_text(
        "منوی سریع فعال شد 👇 (کنار جعبه‌ی نوشتن)",
        reply_markup=reply_keyboard_markup(user.id)
    )
    await update.message.reply_text(
        "سلام 👋 به فروشگاه VPN خوش اومدی!\n\n"
        "پلن‌های پرسرعت، پایدار و ۶ کاربره با بهترین قیمت 🔥\n"
        "یکی از گزینه‌های زیر رو انتخاب کن 👇",
        reply_markup=main_menu_keyboard(user.id)
    )


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    if not await is_member_of_channel(user.id, context):
        await query.answer("هنوز عضو کانال نشدی! اول عضو شو 🙏", show_alert=True)
        return

    await query.answer("خوش اومدی! ✅")
    await query.edit_message_text(
        "سلام 👋 به فروشگاه VPN خوش اومدی!\n\n"
        "پلن‌های پرسرعت، پایدار و ۶ کاربره با بهترین قیمت 🔥\n"
        "یکی از گزینه‌های زیر رو انتخاب کن 👇",
        reply_markup=main_menu_keyboard(user.id)
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"آیدی عددی شما: {update.effective_chat.id}")


# ===================== متن‌های مشترک (برای منوی اینلاین و کیبورد پایین) =====================
def build_stats_text():
    total_users = len(users)
    pending_count = len(pending_orders)
    total_wallet = sum(v["wallet"] for v in users.values())
    total_refs = sum(v["ref_count"] for v in users.values())
    return (
        "📊 <b>آمار ربات</b>\n\n"
        f"👥 تعداد کل کاربران: <b>{total_users}</b>\n"
        f"🕓 سفارش‌های در انتظار بررسی: <b>{pending_count}</b>\n"
        f"👤 مجموع زیرمجموعه‌گیری‌ها: <b>{total_refs}</b>\n"
        f"💰 مجموع موجودی کیف پول همه کاربران: <b>{total_wallet:,} تومان</b>"
    )


def build_referral_text(u, invite_link):
    return (
        "👥 <b>زیرمجموعه‌گیری</b>\n\n"
        "لینک اختصاصی دعوت خودت رو برای دوستات بفرست. به ازای هر نفری که با "
        "لینک تو وارد بشه و خرید انجام بده:\n"
        f"🎖 {REFERRAL_POINT_REWARD} امتیاز\n"
        f"💰 {REFERRAL_WALLET_REWARD:,} تومان اعتبار به کیف پولت اضافه میشه که "
        "می‌تونی توی خریدهای بعدی ازش استفاده کنی.\n\n"
        f"🔗 لینک دعوت شما:\n<code>{invite_link}</code>\n\n"
        f"👤 تعداد زیرمجموعه‌ها: {u['ref_count']}\n"
        f"🎖 امتیاز شما: {u['points']}\n"
        f"💰 موجودی کیف پول: {u['wallet']:,} تومان"
    )


def build_wallet_text(u):
    return (
        "💰 <b>کیف پول</b>\n\n"
        f"موجودی فعلی شما: <b>{u['wallet']:,} تومان</b>\n\n"
        "از موجودی کیف پول می‌تونی موقع خرید یا تمدید اشتراک استفاده کنی، "
        "یا اینکه شارژش کنی."
    )


SUPPORT_TEXT = (
    "🧑 <b>ارتباط با پشتیبانی</b>\n\n"
    f"برای هرگونه سوال یا مشکل با آیدی زیر در ارتباط باش:\n{SUPPORT_USERNAME}"
)


# ===================== روتر منوی اصلی =====================
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    u = get_user(user.id)
    action = query.data

    if action == "menu_main":
        await query.edit_message_text(
            "منوی اصلی 👇",
            reply_markup=main_menu_keyboard(user.id)
        )

    elif action == "menu_stats":
        if user.id != ADMIN_ID:
            await query.answer("این بخش فقط برای ادمینه.", show_alert=True)
            return
        await query.edit_message_text(build_stats_text(), parse_mode="HTML", reply_markup=back_button())

    elif action == "menu_buy":
        pending_orders.pop(user.id, None)
        await query.edit_message_text(
            "🎁 لطفاً یکی از پلن‌های زیر رو برای خرید انتخاب کن 👇",
            reply_markup=plans_keyboard("buy")
        )

    elif action == "menu_renew":
        pending_orders.pop(user.id, None)
        await query.edit_message_text(
            "🔄 لطفاً پلنی که می‌خوای تمدید کنی رو انتخاب کن 👇",
            reply_markup=plans_keyboard("renew")
        )

    elif action == "menu_referral":
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start=REF{user.id}"
        await query.edit_message_text(
            build_referral_text(u, invite_link), parse_mode="HTML", reply_markup=back_button()
        )

    elif action == "menu_wallet":
        await query.edit_message_text(
            build_wallet_text(u), parse_mode="HTML", reply_markup=wallet_menu_keyboard()
        )

    elif action == "menu_support":
        await query.edit_message_text(SUPPORT_TEXT, parse_mode="HTML", reply_markup=back_button())

    elif action == "menu_guide":
        await query.edit_message_text(CONNECTION_GUIDE_TEXT, parse_mode="HTML", reply_markup=back_button())


# ===================== شارژ کیف پول =====================
async def wallet_topup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    pending_orders[user_id] = {
        "mode": "wallet", "plan": None, "name": None,
        "amount": None, "wallet_used": 0, "stage": "awaiting_amount"
    }

    await query.edit_message_text(
        "➕ لطفاً مبلغی که می‌خوای به کیف پولت شارژ کنی رو به تومان (فقط عدد) بفرست.\n"
        "مثال: 100000",
        reply_markup=back_button("menu_wallet")
    )


# ===================== انتخاب پلن (خرید/تمدید) =====================
async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, mode, key = query.data.split("_", 2)
    plan = PLANS[key]
    user_id = query.from_user.id

    pending_orders[user_id] = {
        "mode": mode, "plan": key, "name": None,
        "amount": None, "wallet_used": 0, "stage": "awaiting_name"
    }

    text = (
        f"✅ پلن انتخابی: {plan['button']}\n"
        f"💰 قیمت: {plan['price']:,} تومان\n\n"
        "✏️ لطفاً یک اسم یا آیدی دلخواه (انگلیسی و بدون فاصله) برای اکانت VPN خودت "
        "توی یک پیام برام بفرست. این اسم به عنوان شناسه اکانتت ثبت میشه."
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_button("menu_main"))


# ===================== پیام‌های متنی کاربر (غیر از ادمین) =====================
async def text_message_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order = pending_orders.get(user.id)

    # ---- مرحله‌ی وارد کردن مبلغ شارژ کیف پول ----
    if order and order["mode"] == "wallet" and order["stage"] == "awaiting_amount":
        raw = update.message.text.strip().replace(",", "")
        if not raw.isdigit() or int(raw) <= 0:
            await update.message.reply_text("❗️ لطفاً فقط عدد صحیح و بزرگتر از صفر بفرست. مثال: 100000")
            return

        amount = int(raw)
        order["amount"] = amount
        order["stage"] = "awaiting_receipt"

        text = (
            f"💳 لطفاً مبلغ <b>{amount:,} تومان</b> رو به شماره کارت زیر واریز کن:\n"
            f"<code>{CARD_NUMBER}</code>\n"
            "بعد از واریز، عکس رسید پرداخت رو همینجا برام بفرست."
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    # ---- مرحله‌ی وارد کردن اسم اکانت (خرید/تمدید) ----
    if order and order["mode"] in ("buy", "renew") and order["stage"] == "awaiting_name":
        account_name = update.message.text.strip()
        order["name"] = account_name
        order["stage"] = "awaiting_receipt"

        plan = PLANS[order["plan"]]
        u = get_user(user.id)
        wallet_used = min(u["wallet"], plan["price"])
        amount_to_pay = plan["price"] - wallet_used
        order["wallet_used"] = wallet_used
        order["amount"] = amount_to_pay

        text = f"👤 اسم اکانت ثبت شد: <code>{account_name}</code>\n\n"
        if wallet_used > 0:
            text += (
                f"💰 {wallet_used:,} تومان از موجودی کیف پولت کسر و به عنوان تخفیف اعمال میشه.\n"
            )
        text += (
            f"💳 مبلغ باقی‌مانده برای واریز: <b>{amount_to_pay:,} تومان</b>\n"
            f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
            "بعد از واریز، عکس رسید پرداخت رو همینجا برام بفرست تا سفارشت "
            "برای تایید نهایی برای ادمین ارسال بشه ✅"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return

    # ---- کاربر منتظر ارسال عکس رسیده، ولی متن فرستاده ----
    if order and order["stage"] == "awaiting_receipt":
        await update.message.reply_text(
            "📷 لطفاً به‌جای متن، عکس رسید پرداخت رو ارسال کن.",
            reply_markup=back_button("menu_main", "🔙 بازگشت به منوی اصلی")
        )
        return

    # ---- هیچ‌کدوم از حالت‌های بالا نبود: پیام نامفهوم ----
    await update.message.reply_text(
        "🤔 متوجه نشدم چی گفتی. لطفاً از دکمه‌های منو استفاده کن.",
        reply_markup=back_button("menu_main", "🔙 بازگشت به منوی اصلی")
    )


# ===================== دریافت رسید پرداخت (عکس) =====================
async def receipt_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    order = pending_orders.get(user.id)

    if not order or order.get("stage") != "awaiting_receipt":
        await update.message.reply_text(
            "لطفاً اول از منوی اصلی یکی از گزینه‌ها رو انتخاب کن."
        )
        return

    photo_file_id = update.message.photo[-1].file_id

    if order["mode"] == "wallet":
        caption = (
            "🆕 درخواست شارژ کیف پول\n\n"
            f"👤 کاربر: {user.full_name}\n"
            f"🔗 یوزرنیم: @{user.username if user.username else 'ندارد'} (ID: {user.id})\n"
            f"💰 مبلغ: {order['amount']:,} تومان"
        )
        keyboard = [[
            InlineKeyboardButton("✅ تایید شارژ", callback_data=f"walletconfirm_{user.id}"),
            InlineKeyboardButton("❌ رد شارژ", callback_data=f"walletreject_{user.id}")
        ]]
    else:
        plan = PLANS[order["plan"]]
        caption = (
            f"🆕 سفارش جدید ({MODE_TITLE[order['mode']]})\n\n"
            f"👤 کاربر: {user.full_name}\n"
            f"🔗 یوزرنیم: @{user.username if user.username else 'ندارد'} (ID: {user.id})\n"
            f"🆔 اسم اکانت VPN: {order['name']}\n"
            f"📦 پلن: {plan['button']}\n"
            f"💰 مبلغ کل: {plan['price']:,} تومان\n"
            f"💳 پرداخت‌شده (کارت): {order['amount']:,} تومان\n"
            f"💰 استفاده از کیف پول: {order['wallet_used']:,} تومان"
        )
        keyboard = [[
            InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"orderconfirm_{user.id}"),
            InlineKeyboardButton("❌ رد سفارش", callback_data=f"orderreject_{user.id}")
        ]]

    if ADMIN_ID:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("⚠️ آیدی ادمین هنوز توی کد تنظیم نشده.")
        return

    await update.message.reply_text(
        "✅ رسید شما دریافت شد و برای تایید نهایی برای ادمین ارسال شد.\n"
        "لطفاً کمی صبر کن، به‌زودی نتیجه رو بهت اعلام می‌کنم."
    )


# ===================== تصمیم ادمین (تایید / رد) =====================
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, user_id_str = query.data.split("_")
    user_id = int(user_id_str)
    order = pending_orders.get(user_id, {})
    u = get_user(user_id)

    if action == "orderconfirm":
        wallet_used = order.get("wallet_used", 0)
        if wallet_used:
            u["wallet"] -= wallet_used
        u["purchase_count"] = u.get("purchase_count", 0) + 1

        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 پرداخت شما تایید شد!\nسرویس شما به‌زودی برات ارسال میشه، ممنون از خریدت 🙏"
        )
        new_caption = (query.message.caption or "") + "\n\n✅ تایید شد"

        waiting_for_config[query.from_user.id] = {
            "user_id": user_id, "mode": order.get("mode"), "plan": order.get("plan"),
            "name": order.get("name")
        }
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=(
                "✅ سفارش تایید شد.\n"
                "حالا لطفاً لینک یا کانفیگ VPN این کاربر رو توی یک پیام برام بفرست "
                "تا مستقیم براش ارسال بشه."
            )
        )

    elif action == "orderreject":
        # نکته: چون کسر شدن از کیف پول فقط توی orderconfirm انجام میشه، اینجا
        # (رد سفارش) چیزی برای برگردوندن نیست؛ کیف پول کاربر اصلاً دست‌نخورده مونده.
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ متاسفانه رسید پرداخت شما تایید نشد.\n"
                f"لطفاً با پشتیبانی در ارتباط باش: {SUPPORT_USERNAME}"
            )
        )
        new_caption = (query.message.caption or "") + "\n\n❌ رد شد"

    elif action == "walletconfirm":
        amount = order.get("amount", 0)
        u["wallet"] += amount
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 شارژ کیف پول شما تایید شد!\nموجودی جدید: {u['wallet']:,} تومان"
        )
        new_caption = (query.message.caption or "") + "\n\n✅ تایید شد"

    else:  # walletreject
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ متاسفانه رسید شارژ کیف پول تایید نشد.\n"
                f"لطفاً با پشتیبانی در ارتباط باش: {SUPPORT_USERNAME}"
            )
        )
        new_caption = (query.message.caption or "") + "\n\n❌ رد شد"

    await query.edit_message_caption(caption=new_caption)
    pending_orders.pop(user_id, None)


# ===================== ارسال لینک VPN از ادمین به کاربر =====================
def broadcast_target_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌍 همه کاربران", callback_data="bcast_target_all")],
        [InlineKeyboardButton("🛍 فقط کسایی که خرید کردن", callback_data="bcast_target_buyers")],
        [InlineKeyboardButton("🌱 کسایی که هنوز خرید نکردن", callback_data="bcast_target_non_buyers")],
        [InlineKeyboardButton("❌ انصراف", callback_data="bcast_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def broadcast_confirm_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ ارسال کن", callback_data="bcast_confirm")],
        [InlineKeyboardButton("❌ انصراف", callback_data="bcast_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_broadcast_recipients(target):
    if target == "all":
        return list(users.keys())
    if target == "buyers":
        return [uid for uid, u in users.items() if u.get("purchase_count", 0) > 0]
    if target == "non_buyers":
        return [uid for uid, u in users.items() if u.get("purchase_count", 0) == 0]
    return []


TARGET_LABELS = {
    "all": "🌍 همه کاربران",
    "buyers": "🛍 فقط خریداران",
    "non_buyers": "🌱 کسایی که هنوز خرید نکردن",
}


async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id

    if admin_id != ADMIN_ID:
        await query.answer("این بخش فقط برای ادمینه.", show_alert=True)
        return

    data = query.data

    if data == "bcast_cancel":
        broadcast_state.pop(admin_id, None)
        await query.edit_message_text("❌ ارسال پیام همگانی لغو شد.")
        return

    if data.startswith("bcast_target_"):
        target = data[len("bcast_target_"):]
        recipients = get_broadcast_recipients(target)
        broadcast_state[admin_id] = {"stage": "awaiting_text", "target": target}
        await query.edit_message_text(
            f"گروه انتخابی: {TARGET_LABELS.get(target, target)} ({len(recipients)} نفر)\n\n"
            "حالا متن پیامی که می‌خوای ارسال بشه رو برام بفرست."
        )
        return

    if data == "bcast_confirm":
        state = broadcast_state.get(admin_id)
        if not state or state.get("stage") != "awaiting_confirm":
            await query.edit_message_text("چیزی برای ارسال پیدا نشد. دوباره از اول امتحان کن.")
            return

        target = state["target"]
        message_text = state["text"]
        recipients = get_broadcast_recipients(target)
        broadcast_state.pop(admin_id, None)

        await query.edit_message_text(f"⏳ در حال ارسال به {len(recipients)} نفر... (این پیام بعد از اتمام آپدیت میشه)")

        success, failed = 0, 0
        for uid in recipients:
            try:
                await context.bot.send_message(chat_id=uid, text=message_text)
                success += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.05)  # جلوگیری از محدودیت ارسال سریع تلگرام

        await query.edit_message_text(
            "✅ ارسال پیام همگانی تموم شد.\n\n"
            f"👥 گروه: {TARGET_LABELS.get(target, target)}\n"
            f"✅ موفق: {success}\n"
            f"❌ ناموفق (مثلاً بات رو بلاک کردن): {failed}"
        )


async def broadcast_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """اگه ادمین توی مرحله‌ی نوشتن متن پیام همگانیه، این تابع پیامش رو می‌گیره.
    True برمی‌گردونه یعنی پیام رو مصرف کرده و نباید هندلر بعدی روش اجرا بشه."""
    admin_id = update.effective_user.id
    state = broadcast_state.get(admin_id)
    if not state or state.get("stage") != "awaiting_text":
        return False

    message_text = update.message.text
    if not message_text:
        await update.message.reply_text("لطفاً متن پیام رو به‌صورت نوشتاری بفرست.")
        return True

    target = state["target"]
    recipients = get_broadcast_recipients(target)
    broadcast_state[admin_id] = {"stage": "awaiting_confirm", "target": target, "text": message_text}

    preview = (
        "📢 <b>پیش‌نمایش پیام همگانی</b>\n\n"
        f"👥 گروه: {TARGET_LABELS.get(target, target)} ({len(recipients)} نفر)\n\n"
        "متن پیام:\n"
        "――――――――――\n"
        f"{message_text}\n"
        "――――――――――\n\n"
        "ارسال بشه؟"
    )
    await update.message.reply_text(preview, parse_mode="HTML", reply_markup=broadcast_confirm_keyboard())
    return True


def direct_msg_confirm_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ ارسال کن", callback_data="dmsg_confirm")],
        [InlineKeyboardButton("❌ انصراف", callback_data="dmsg_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def direct_msg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id

    if admin_id != ADMIN_ID:
        await query.answer("این بخش فقط برای ادمینه.", show_alert=True)
        return

    data = query.data

    if data == "dmsg_cancel":
        direct_msg_state.pop(admin_id, None)
        await query.edit_message_text("❌ ارسال پیام لغو شد.")
        return

    if data == "dmsg_confirm":
        state = direct_msg_state.get(admin_id)
        if not state or state.get("stage") != "awaiting_confirm":
            await query.edit_message_text("چیزی برای ارسال پیدا نشد. دوباره از اول امتحان کن.")
            return

        target_id = state["target_id"]
        message_text = state["text"]
        direct_msg_state.pop(admin_id, None)

        try:
            await context.bot.send_message(chat_id=target_id, text=message_text)
            target_u = users.get(target_id, {})
            uname = f"@{target_u['username']}" if target_u.get("username") else str(target_id)
            await query.edit_message_text(f"✅ پیام با موفقیت برای {uname} ارسال شد.")
        except Exception:
            await query.edit_message_text("❌ ارسال پیام ناموفق بود (احتمالاً کاربر بات رو بلاک کرده).")


async def direct_msg_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """اگه ادمین توی مراحل «پیام به کاربر خاص» باشه، پیامش رو اینجا مدیریت می‌کنیم.
    True یعنی پیام مصرف شد و نباید هندلر بعدی روش اجرا بشه."""
    admin_id = update.effective_user.id
    state = direct_msg_state.get(admin_id)
    if not state:
        return False

    stage = state.get("stage")
    message_text = update.message.text

    if stage == "awaiting_target":
        if not message_text:
            await update.message.reply_text("لطفاً یوزرنیم یا آیدی عددی رو به‌صورت متن بفرست.")
            return True

        query_text = message_text.strip()
        target_id = None
        if query_text.lstrip("-").isdigit():
            candidate = int(query_text)
            if candidate in users:
                target_id = candidate
        else:
            target_id = find_user_by_username(query_text)

        if target_id is None:
            await update.message.reply_text(
                "❌ همچین کاربری بین کاربرای شناخته‌شده‌ی ربات پیدا نشد.\n"
                "مطمئن شو یوزرنیم رو درست وارد کردی و اون کاربر حداقل یک‌بار /start زده.\n"
                "دوباره امتحان کن یا برای انصراف چیز دیگه‌ای بنویس."
            )
            return True

        target_u = users[target_id]
        uname = f"@{target_u['username']}" if target_u.get("username") else "بدون یوزرنیم"
        direct_msg_state[admin_id] = {"stage": "awaiting_text", "target_id": target_id}
        await update.message.reply_text(
            f"✅ کاربر پیدا شد: {uname} (ID: {target_id})\n"
            f"🛍 تعداد خرید: {target_u.get('purchase_count', 0)}\n\n"
            "حالا متن پیامی که می‌خوای براش بفرستم رو بنویس."
        )
        return True

    if stage == "awaiting_text":
        if not message_text:
            await update.message.reply_text("لطفاً متن پیام رو به‌صورت نوشتاری بفرست.")
            return True

        target_id = state["target_id"]
        target_u = users.get(target_id, {})
        uname = f"@{target_u.get('username')}" if target_u.get("username") else str(target_id)
        direct_msg_state[admin_id] = {"stage": "awaiting_confirm", "target_id": target_id, "text": message_text}

        preview = (
            "✉️ <b>پیش‌نمایش پیام</b>\n\n"
            f"👤 گیرنده: {uname}\n\n"
            "متن پیام:\n"
            "――――――――――\n"
            f"{message_text}\n"
            "――――――――――\n\n"
            "ارسال بشه؟"
        )
        await update.message.reply_text(preview, parse_mode="HTML", reply_markup=direct_msg_confirm_keyboard())
        return True

    return False


async def forward_config_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id

    if await broadcast_text_received(update, context):
        return

    if await direct_msg_text_received(update, context):
        return

    if admin_id not in waiting_for_config:
        return

    info = waiting_for_config.pop(admin_id)
    user_id = info["user_id"]
    plan_key = info.get("plan")
    config_text = update.message.text

    await context.bot.send_message(
        chat_id=user_id,
        text=f"🔗 لینک/کانفیگ VPN شما:\n\n{config_text}\n\nممنون از خریدت 🌐"
    )
    await update.message.reply_text("✅ لینک با موفقیت برای کاربر ارسال شد.")

    # پاداش زیرمجموعه‌گیری برای دعوت‌کننده
    if plan_key and plan_key in PLANS:
        buyer = get_user(user_id)
        referrer_id = buyer.get("referred_by")
        if referrer_id and referrer_id in users:
            referrer = users[referrer_id]
            referrer["wallet"] += REFERRAL_WALLET_REWARD
            referrer["points"] += REFERRAL_POINT_REWARD
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        "🎉 یکی از زیرمجموعه‌های شما خرید موفق داشت!\n"
                        f"🎖 {REFERRAL_POINT_REWARD} امتیاز و 💰 {REFERRAL_WALLET_REWARD:,} تومان "
                        "به کیف پولت اضافه شد."
                    )
                )
            except Exception:
                pass


# ===================== پیام‌های زمان‌بندی‌شده =====================
async def send_morning_message(context: ContextTypes.DEFAULT_TYPE):
    for user_id in list(users.keys()):
        try:
            await context.bot.send_message(chat_id=user_id, text=MORNING_MESSAGE, parse_mode="HTML")
        except Exception:
            pass  # مثلاً کاربر بات رو بلاک کرده


async def send_promo_message(context: ContextTypes.DEFAULT_TYPE):
    for user_id in list(users.keys()):
        try:
            await context.bot.send_message(chat_id=user_id, text=PROMO_MESSAGE, parse_mode="HTML")
        except Exception:
            pass


# ===================== اجرای بات =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # پیام صبح‌بخیر هر روز ساعت ۸ صبح (به وقت سرور)
    app.job_queue.run_daily(
        send_morning_message,
        time=datetime.time(hour=8, minute=0, second=0),
        name="morning_message",
    )

    # پیام تبلیغاتی هر ۳ روز یک‌بار
    app.job_queue.run_repeating(
        send_promo_message,
        interval=datetime.timedelta(days=3),
        first=datetime.timedelta(days=3),
        name="promo_message",
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(wallet_topup_start, pattern="^wallet_topup$"))
    app.add_handler(CallbackQueryHandler(plan_selected, pattern="^plan_"))
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^(orderconfirm|orderreject|walletconfirm|walletreject)_"))
    app.add_handler(CallbackQueryHandler(broadcast_callback, pattern="^bcast_"))
    app.add_handler(CallbackQueryHandler(direct_msg_callback, pattern="^dmsg_"))

    # دکمه‌های کیبورد پایین (باید قبل از هندلرهای متنی عمومی چک بشه تا اولویت داشته باشه)
    reply_buttons_pattern = "^(" + "|".join(
        re.escape(b) for b in [BTN_BUY, BTN_RENEW, BTN_WALLET, BTN_REFERRAL, BTN_SUPPORT, BTN_GUIDE, BTN_STATS, BTN_BROADCAST, BTN_DIRECT_MSG]
    ) + ")$"
    app.add_handler(MessageHandler(filters.Regex(reply_buttons_pattern), reply_menu_router))

    app.add_handler(MessageHandler(filters.PHOTO, receipt_received))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.Chat(ADMIN_ID) & ~filters.COMMAND, forward_config_to_user)
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.Chat(ADMIN_ID) & ~filters.COMMAND, text_message_received)
    )

    print("بات فروش VPN در حال اجراست... برای توقف Ctrl+C بزن")
    app.run_polling()


if __name__ == "__main__":
    main()
