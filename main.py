import asyncio
import logging
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from utils.db import Database
import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(config.DB_NAME)

class Registration(StatesGroup):
    language = State()
    name = State()
    age = State()
    gender = State()
    region = State()
    photo = State()

class SearchState(StatesGroup):
    browsing = State()

# --- Klaviaturalar ---
def get_main_menu():
    kb = [[types.KeyboardButton(text="Qidiruv 🔍"), types.KeyboardButton(text="Profilim 👤")],
          [types.KeyboardButton(text="Sozlamalar ⚙️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_gender_kb():
    kb = [[types.KeyboardButton(text="Yigit 🧒"), types.KeyboardButton(text="Qiz 🧕")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_search_kb():
    kb = [[types.KeyboardButton(text="Yigit topish 🧒"), types.KeyboardButton(text="Qiz topish 🧕")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- Handlerlar ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        kb = [[types.KeyboardButton(text="O'zbekcha 🇺🇿"), types.KeyboardButton(text="English 🇺🇸")]]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("Tilni tanlang / Select language:", reply_markup=markup)
        await state.set_state(Registration.language)
    else:
        await message.answer("Xush kelibsiz!", reply_markup=get_main_menu())

@dp.message(Registration.language)
async def set_lang(message: types.Message, state: FSMContext):
    lang = "uz" if "O'zbekcha" in message.text else "en"
    db.add_user(message.from_user.id, message.from_user.username, lang)
    await message.answer("Ismingizni kiriting:")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def set_name(message: types.Message, state: FSMContext):
    db.update_user(message.from_user.id, full_name=message.text)
    await message.answer("Yoshingizni kiriting:")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def set_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Iltimos, faqat raqam kiriting:")
    db.update_user(message.from_user.id, age=int(message.text))
    await message.answer("Jinsingizni tanlang:", reply_markup=get_gender_kb())
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def set_gender(message: types.Message, state: FSMContext):
    gender = "male" if "Yigit" in message.text else "female"
    db.update_user(message.from_user.id, gender=gender)
    kb = [[types.KeyboardButton(text=r)] for r in config.REGIONS[:6]] # Birinchi 6 ta viloyat
    markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Viloyatingizni tanlang:", reply_markup=markup)
    await state.set_state(Registration.region)

@dp.message(Registration.region)
async def set_region(message: types.Message, state: FSMContext):
    db.update_user(message.from_user.id, region=message.text)
    await message.answer("Profilingiz uchun rasm yuboring:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def set_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    db.update_user(message.from_user.id, photo=photo_id)
    await message.answer("Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!", reply_markup=get_main_menu())
    await state.clear()

# --- Qidiruv va Profil ---
@dp.message(F.text == "Qidiruv 🔍")
async def search_menu(message: types.Message):
    await message.answer("Kimni qidiramiz?", reply_markup=get_search_kb())

@dp.message(F.text.in_(["Yigit topish 🧒", "Qiz topish 🧕"]))
async def find_partner(message: types.Message):
    gender = "male" if "Yigit" in message.text else "female"
    users = db.get_random_users(gender)
    if not users:
        return await message.answer("Hozircha hech kim topilmadi.")
    
    user = random.choice(users)
    caption = f"👤 {user[2]}, {user[3]} yosh\n📍 {user[5]}"
    if user[7]: # photo
        await message.answer_photo(user[7], caption=caption)
    else:
        await message.answer(caption)

@dp.message(F.text == "Profilim 👤")
async def my_profile(message: types.Message):
    user = db.get_user(message.from_user.id)
    caption = f"Sizning profilingiz:\n\n👤 Ism: {user[2]}\n🔢 Yosh: {user[3]}\n📍 Viloyat: {user[5]}"
    if user[7]:
        await message.answer_photo(user[7], caption=caption)
    else:
        await message.answer(caption)

# Link filtri
@dp.message(F.text.contains("t.me") | F.text.contains("http") | F.text.contains("@"))
async def link_filter(message: types.Message):
    await message.delete()
    await message.answer("Link yuborish taqiqlangan! 🚫")

# Render uchun veb-server
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
