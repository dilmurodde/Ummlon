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

# Logging
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher
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

# --- Klaviaturalar ---
def get_main_menu():
    kb = [[types.KeyboardButton(text="Qidiruv 🔍"), types.KeyboardButton(text="Profilim 👤")],
          [types.KeyboardButton(text="Sozlamalar ⚙️")]]
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

# Linklarni bloklash
@dp.message(F.text.contains("t.me") | F.text.contains("http") | F.text.contains("@"))
async def link_filter(message: types.Message):
    await message.delete()
    await message.answer("Link yuborish taqiqlangan! 🚫")

# Render uchun soxta veb-server
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    # Veb-serverni alohida vazifa sifatida ishga tushiramiz
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await site.start()
    
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
