import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("COINMARKETCAP_API_KEY")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

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
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Получить архив актуальных цен", callback_data="get_prices"))
    keyboard.add(InlineKeyboardButton("Цена криптовалюты по названию", callback_data="get_crypto_by_name"))
    keyboard.add(InlineKeyboardButton("Топ-10 криптовалют", callback_data="top_cryptos"))
    keyboard.add(InlineKeyboardButton("О боте", callback_data="about_bot"))
    return keyboard

# Команда /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Привет! Я бот для отслеживания цен на криптовалюты. Выберите действие:", reply_markup=main_keyboard())

# Обработка кнопок
@dp.callback_query_handler(Text(startswith="get_prices"))
async def get_prices(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Получение цен...")
    prices = get_crypto_prices()
    await callback_query.message.answer(f"Актуальные цены:\n\n{prices}")

@dp.callback_query_handler(Text(startswith="get_crypto_by_name"))
async def ask_crypto_name(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Введите название криптовалюты (например, Bitcoin):")

@dp.message_handler()
async def handle_crypto_name(message: types.Message):
    name = message.text.strip()
    result = get_crypto_price_by_name(name)
    await message.answer(result)

@dp.callback_query_handler(Text(startswith="top_cryptos"))
async def get_top_cryptos(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Получение Топ-10 криптовалют...")
    top_cryptos = get_crypto_prices(limit=10)
    await callback_query.message.answer(f"Топ-10 криптовалют:\n\n{top_cryptos}")

@dp.callback_query_handler(Text(startswith="about_bot"))
async def about_bot(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Этот бот позволяет отслеживать цены на криптовалюты в реальном времени. Выберите действие на клавиатуре!")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
