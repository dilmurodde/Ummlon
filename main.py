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
    language, name, age, gender, region, photo = State(), State(), State(), State(), State(), State()

class EditProfile(StatesGroup):
    choosing_field = State()
    updating_value = State()

class SearchState(StatesGroup):
    browsing = State()
    chatting = State()

# --- Klaviaturalar ---
def get_main_menu():
    kb = [[types.KeyboardButton(text="Qidiruv 🔍"), types.KeyboardButton(text="Profilim 👤")],
          [types.KeyboardButton(text="Sozlamalar ⚙️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_kb():
    kb = [[types.KeyboardButton(text="Profilni tahrirlash 📝")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_edit_fields_kb():
    kb = [[types.KeyboardButton(text="Ismni o'zgartirish"), types.KeyboardButton(text="Yoshni o'zgartirish")],
          [types.KeyboardButton(text="Viloyatni o'zgartirish"), types.KeyboardButton(text="Rasmni o'zgartirish")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_regions_kb():
    buttons = [types.KeyboardButton(text=r) for r in config.REGIONS]
    kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    kb.append([types.KeyboardButton(text="Orqaga ⬅️")])
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_search_kb():
    kb = [[types.KeyboardButton(text="Yigit topish 🧒"), types.KeyboardButton(text="Qiz topish 🧕")],
          [types.KeyboardButton(text="Orqaga ⬅️")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_chat_kb():
    kb = [[types.KeyboardButton(text="Xabar yuborish ✉️"), types.KeyboardButton(text="Keyingisi ⏭")],
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

@dp.message(F.text == "Orqaga ⬅️")
async def go_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu())

# --- Ro'yxatdan o'tish bosqichlari ---
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
    if not message.text.isdigit(): return await message.answer("Faqat raqam kiriting:")
    db.update_user(message.from_user.id, age=int(message.text))
    kb = [[types.KeyboardButton(text="Yigit 🧒"), types.KeyboardButton(text="Qiz 🧕")]]
    await message.answer("Jinsingizni tanlang:", reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(Registration.gender)

@dp.message(Registration.gender)
async def set_gender(message: types.Message, state: FSMContext):
    gender = "male" if "Yigit" in message.text else "female"
    db.update_user(message.from_user.id, gender=gender)
    await message.answer("Viloyatingizni tanlang:", reply_markup=get_regions_kb())
    await state.set_state(Registration.region)

@dp.message(Registration.region)
async def set_region(message: types.Message, state: FSMContext):
    db.update_user(message.from_user.id, region=message.text)
    await message.answer("Profilingiz uchun rasm yuboring:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def set_photo(message: types.Message, state: FSMContext):
    db.update_user(message.from_user.id, photo=message.photo[-1].file_id)
    await message.answer("Tayyor! ✅", reply_markup=get_main_menu())
    await state.clear()

# --- Profilni tahrirlash ---
@dp.message(F.text == "Profilim 👤")
async def my_profile(message: types.Message):
    user = db.get_user(message.from_user.id)
    caption = f"👤 Ism: {user[2]}\n🔢 Yosh: {user[3]}\n📍 Viloyat: {user[5]}"
    if user[7]: await message.answer_photo(user[7], caption=caption, reply_markup=get_profile_kb())
    else: await message.answer(caption, reply_markup=get_profile_kb())

@dp.message(F.text == "Profilni tahrirlash 📝")
async def edit_profile(message: types.Message, state: FSMContext):
    await message.answer("Nimani o'zgartiramiz?", reply_markup=get_edit_fields_kb())
    await state.set_state(EditProfile.choosing_field)

@dp.message(EditProfile.choosing_field)
async def choose_field(message: types.Message, state: FSMContext):
    if "Ism" in message.text:
        await message.answer("Yangi ismni kiriting:")
        await state.update_data(field="full_name")
    elif "Yosh" in message.text:
        await message.answer("Yangi yoshni kiriting:")
        await state.update_data(field="age")
    elif "Viloyat" in message.text:
        await message.answer("Yangi viloyatni tanlang:", reply_markup=get_regions_kb())
        await state.update_data(field="region")
    elif "Rasm" in message.text:
        await message.answer("Yangi rasm yuboring:")
        await state.update_data(field="photo")
    else: return
    await state.set_state(EditProfile.updating_value)

@dp.message(EditProfile.updating_value)
async def update_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data['field']
    val = message.photo[-1].file_id if field == "photo" and message.photo else message.text
    db.update_user(message.from_user.id, **{field: val})
    await message.answer("O'zgartirildi! ✅", reply_markup=get_main_menu())
    await state.clear()

# --- Qidiruv va Chat ---
@dp.message(F.text == "Qidiruv 🔍")
async def search_menu(message: types.Message):
    await message.answer("Kimni qidiramiz?", reply_markup=get_search_kb())

@dp.message(F.text.in_(["Yigit topish 🧒", "Qiz topish 🧕"]))
async def find_partner(message: types.Message, state: FSMContext):
    gender = "male" if "Yigit" in message.text else "female"
    users = db.get_random_users(gender)
    if not users: return await message.answer("Hech kim topilmadi.")
    user = random.choice(users)
    await state.update_data(target_id=user[0], is_fake=user[9])
    caption = f"👤 {user[2]}, {user[3]} yosh\n📍 {user[5]}"
    if user[7]: await message.answer_photo(user[7], caption=caption, reply_markup=get_chat_kb())
    else: await message.answer(caption, reply_markup=get_chat_kb())
    await state.set_state(SearchState.browsing)

@dp.message(SearchState.browsing)
async def browsing(message: types.Message, state: FSMContext):
    if message.text == "Keyingisi ⏭": await find_partner(message, state)
    elif message.text == "Xabar yuborish ✉️":
        await message.answer("Xabaringizni yozing:")
        await state.set_state(SearchState.chatting)
    else: await go_back(message, state)

@dp.message(SearchState.chatting)
async def chatting(message: types.Message, state: FSMContext):
    if any(x in message.text.lower() for x in ['t.me', 'http', '@']):
        await message.delete()
        return await message.answer("Link taqiqlangan! 🚫")
    
    data = await state.get_data()
    await message.answer("Xabar yuborildi! ✅")
    if data.get('is_fake'):
        await asyncio.sleep(2)
        responses = ["Salom!", "Qayerdansiz?", "Tanishganimdan xursandman 😊"]
        await message.answer(f"Javob: {random.choice(responses)}")
    
    await message.answer("Yana qidiramizmi?", reply_markup=get_search_kb())
    await state.clear()

# Render uchun veb-server
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
    
