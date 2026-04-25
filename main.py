import asyncio
import logging
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from utils.db import Database
import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(config.DB_NAME)

class Registration(StatesGroup):
    language, name, age, gender, region, photo = State(), State(), State(), State(), State(), State()

class SearchState(StatesGroup):
    browsing = State()
    chatting = State()

# --- Klaviaturalar ---
def get_main_menu():
    kb = [[types.KeyboardButton(text="Qidiruv 🔍"), types.KeyboardButton(text="Profilim 👤")],
          [types.KeyboardButton(text="Sozlamalar ⚙️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_chat_buttons(target_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Javob berish ✍️", callback_data=f"reply_{target_id}")
    return builder.as_markup()

# --- Handlerlar ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        kb = [[types.KeyboardButton(text="O'zbekcha 🇺🇿"), types.KeyboardButton(text="English 🇺🇸")]]
        await message.answer("Tilni tanlang:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
        await state.set_state(Registration.language)
    else:
        await message.answer("Xush kelibsiz!", reply_markup=get_main_menu())

# Qidiruv va Xabar yuborish
@dp.message(F.text == "Qidiruv 🔍")
async def search_menu(message: types.Message):
    kb = [[types.KeyboardButton(text="Yigit topish 🧒"), types.KeyboardButton(text="Qiz topish 🧕")], [types.KeyboardButton(text="Orqaga ⬅️")]]
    await message.answer("Kimni qidiramiz?", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.text.in_(["Yigit topish 🧒", "Qiz topish 🧕"]))
async def find_partner(message: types.Message, state: FSMContext):
    gender = "male" if "Yigit" in message.text else "female"
    users = db.get_random_users(gender)
    if not users: return await message.answer("Hech kim topilmadi.")
    user = random.choice(users)
    await state.update_data(target_id=user[0], is_fake=user[9])
    
    kb = [[types.KeyboardButton(text="Xabar yuborish ✉️"), types.KeyboardButton(text="Keyingisi ⏭")], [types.KeyboardButton(text="Orqaga ⬅️")]]
    caption = f"👤 {user[2]}, {user[3]} yosh\n📍 {user[5]}"
    if user[7]: await message.answer_photo(user[7], caption=caption, reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    else: await message.answer(caption, reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(SearchState.browsing)

@dp.message(SearchState.browsing, F.text == "Xabar yuborish ✉️")
async def start_chat(message: types.Message, state: FSMContext):
    await message.answer("Xabaringizni yozing (u odamga darhol boradi):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(SearchState.chatting)

@dp.message(SearchState.chatting)
async def send_message_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get('target_id')
    
    if data.get('is_fake'):
        await message.answer("Xabar yuborildi! ✅")
        await asyncio.sleep(2)
        await message.answer(f"Javob: {random.choice(['Salom!', 'Qayerdansiz?', 'Tanishganimdan xursandman 😊'])}")
    else:
        try:
            # Xabarni yuborish va "Javob berish" tugmasini qo'shish
            await bot.send_message(
                chat_id=target_id, 
                text=f"📩 Yangi xabar!\n\nSiz bilan kimdir suhbatlashmoqchi:\n\"{message.text}\"",
                reply_markup=get_chat_buttons(message.from_user.id)
            )
            await message.answer("Xabaringiz yetkazildi! ✅")
        except:
            await message.answer("Xabar yuborib bo'lmadi. ❌")
    
    await message.answer("Asosiy menyu", reply_markup=get_main_menu())
    await state.clear()

# Javob berish tugmasi bosilganda
@dp.callback_query(F.data.startswith("reply_"))
async def reply_callback(callback: types.CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    await callback.message.answer("Javob xabaringizni yozing:")
    await state.update_data(target_id=target_id)
    await state.set_state(SearchState.chatting)
    await callback.answer()

# Render veb-server
async def handle(request): return web.Response(text="Bot is running!")
async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000))).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
