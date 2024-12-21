import os
import csv
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import asyncio
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("COINMARKETCAP_API_KEY")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Базовый URL API CoinMarketCap
BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# Функция для получения списка криптовалют с ценами
def get_crypto_data(limit=100):
    url = f"{BASE_URL}/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    params = {"start": "1", "limit": limit, "convert": "USD"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        return None

# Генерация CSV-файла
def generate_crypto_csv(data, filename="crypto_prices.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Заголовки
        writer.writerow(["Название", "Тикер", "Цена (USD)", "Объем (24ч)", "Рыночная капитализация"])
        # Заполнение данными
        for crypto in data:
            writer.writerow([
                crypto["name"],
                crypto["symbol"],
                f"{crypto['quote']['USD']['price']:.2f}",
                f"{crypto['quote']['USD']['volume_24h']:.2f}",
                f"{crypto['quote']['USD']['market_cap']:.2f}"
            ])
    return filename

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
        await callback_query.message.answer("Генерация файла с ценами...")
        data = get_crypto_data(limit=100)
        if data:
            filename = generate_crypto_csv(data)
            try:
                # Отправляем файл пользователю
                await callback_query.message.answer_document(
                    document=types.InputFile(path_or_bytesio=filename),
                    caption="Вот файл с актуальными ценами на криптовалюты."
                )
            except Exception as e:
                print(f"Ошибка при отправке файла: {e}")
                await callback_query.message.answer("Произошла ошибка при отправке файла.")
            finally:
                # Удаляем файл после отправки
                if os.path.exists(filename):
                    os.remove(filename)
        else:
            await callback_query.message.answer("Не удалось получить данные. Попробуйте позже.")

# Обработка текстовых сообщений
@dp.message()
async def handle_text_message(message: types.Message):
    name = message.text.strip()
    data = get_crypto_data(limit=100)
    if data:
        for crypto in data:
            if name.lower() in crypto["name"].lower() or name.lower() == crypto["symbol"].lower():
                result = f"{crypto['name']} ({crypto['symbol']}): ${crypto['quote']['USD']['price']:.2f}"
                await message.answer(result)
                return
        await message.answer("Криптовалюта не найдена. Проверьте правильность ввода.")
    else:
        await message.answer("Не удалось получить данные. Попробуйте позже.")

# Запуск бота
async def main():
    # Удаляем webhook и запускаем long polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
