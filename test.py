import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import asyncio
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = "7815154623:AAGkH6TTZW0lt4Z2i6dBa9MLD7mneL-urok"
API_KEY = os.getenv("COINMARKETCAP_API_KEY")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Базовый URL API CoinMarketCap
BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# Функция для получения списка криптовалют с ценами
def get_crypto_prices(limit=10):
    url = f"{BASE_URL}/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    params = {"start": "1", "limit": limit, "convert": "USD"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()["data"]
        prices = [f"{crypto['name']} ({crypto['symbol']}): ${crypto['quote']['USD']['price']:.2f}" for crypto in data]
        return "\n".join(prices)
    else:
        return "Ошибка при получении данных. Попробуйте позже."

# Функция для получения цены конкретной криптовалюты
def get_crypto_price_by_name(name):
    url = f"{BASE_URL}/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    params = {"convert": "USD"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()["data"]
        for crypto in data:
            if name.lower() in crypto["name"].lower() or name.lower() == crypto["symbol"].lower():
                return f"{crypto['name']} ({crypto['symbol']}): ${crypto['quote']['USD']['price']:.2f}"
        return "Криптовалюта не найдена. Проверьте правильность ввода."
    else:
        return "Ошибка при получении данных. Попробуйте позже."

# Главная клавиатура
def main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Получить архив актуальных цен", callback_data="get_prices")
        ],
        [
            InlineKeyboardButton(text="Цена криптовалюты по названию", callback_data="get_crypto_by_name")
        ],
        [
            InlineKeyboardButton(text="Топ-10 криптовалют", callback_data="top_cryptos")
        ],
        [
            InlineKeyboardButton(text="О боте", callback_data="about_bot")
        ]
    ])
    return keyboard


# Обработка команды /start
@dp.message(Command(commands=["start"]))
async def start_command(message: types.Message):
    try:
        await message.answer(
            "Привет! Я бот для отслеживания цен на криптовалюты. Выберите действие:",
            reply_markup=main_keyboard()
        )
    except Exception as e:
        print(f"Ошибка в обработчике /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")



# Обработка callback-запросов
@dp.callback_query()
async def handle_callback(callback_query: types.CallbackQuery):
    if callback_query.data == "get_prices":
        await callback_query.message.answer("Получение цен...")
        prices = get_crypto_prices()
        await callback_query.message.answer(f"Актуальные цены:\n\n{prices}")
    elif callback_query.data == "get_crypto_by_name":
        await callback_query.message.answer("Введите название криптовалюты (например, Bitcoin):")
    elif callback_query.data == "top_cryptos":
        await callback_query.message.answer("Получение Топ-10 криптовалют...")
        top_cryptos = get_crypto_prices(limit=10)
        await callback_query.message.answer(f"Топ-10 криптовалют:\n\n{top_cryptos}")
    elif callback_query.data == "about_bot":
        await callback_query.message.answer("Этот бот позволяет отслеживать цены на криптовалюты в реальном времени. Выберите действие на клавиатуре!")

# Обработка текстовых сообщений
@dp.message()
async def handle_text_message(message: types.Message):
    name = message.text.strip()
    result = get_crypto_price_by_name(name)
    await message.answer(result)

# Запуск бота
async def main():
    # Удаляем webhook и запускаем long polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    
    asyncio.run(main())
