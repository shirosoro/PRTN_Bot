import logging
import json
import aiohttp
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from pathlib import Path
import token_api

# Адрес контракта токена PRTN
PRTN_CONTRACT = "EQBCHMY4xNfQn9tU70qlibOcl8YbSrXb4-J_rAVqeTsAWlJu"
DEXSCREENER_API = f"https://api.dexscreener.com/latest/dex/tokens/{PRTN_CONTRACT}"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание экземпляра бота и диспетчера
bot = Bot(token=token_api.API_TOKEN)
dp = Dispatcher()
router = Router()

# Путь для сохранения языковых настроек
USER_LANG_FILE = Path("user_languages.json")
GROUP_LANG_FILE = Path("group_languages.json")

# Словари для хранения языков
if USER_LANG_FILE.exists():
    with open(USER_LANG_FILE, "r", encoding="utf-8") as file:
        user_languages = json.load(file)
else:
    user_languages = {}

if GROUP_LANG_FILE.exists():
    with open(GROUP_LANG_FILE, "r", encoding="utf-8") as file:
        group_languages = json.load(file)
else:
    group_languages = {}

# Сохранение языковых настроек в файл
def save_user_languages():
    with open(USER_LANG_FILE, "w", encoding="utf-8") as file:
        json.dump(user_languages, file, ensure_ascii=False, indent=4)

def save_group_languages():
    with open(GROUP_LANG_FILE, "w", encoding="utf-8") as file:
        json.dump(group_languages, file, ensure_ascii=False, indent=4)

# Функция для загрузки языковых файлов
def load_language(lang_code):
    lang_file = Path(f"{lang_code}.json")
    if lang_file.exists():
        with open(lang_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Функция для получения данных о токене
async def get_token_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(DEXSCREENER_API) as response:
            if response.status == 200:
                return await response.json()
            return None

# Функция для определения языка
def get_language(chat_id, chat_type):
    if chat_type in ["group", "supergroup"]:
        return group_languages.get(str(chat_id), "en")
    else:
        return user_languages.get(str(chat_id), "en")

# Форматирование чисел с пробелами
def format_number(number):
    try:
        return f"{float(number):,.1f}".replace(",", " ")
    except ValueError:
        return number

# Команда для установки языка группы
@router.message(Command("setgrouplang"))
async def cmd_setgrouplang(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("This command is only available in groups.")
        return

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        await message.answer("Only administrators can set the group language.")
        return

    if "en" in message.text.lower():
        group_languages[str(message.chat.id)] = "en"
        save_group_languages()
        await message.answer("Group language set to English!")
    elif "ru" in message.text.lower():
        group_languages[str(message.chat.id)] = "ru"
        save_group_languages()
        await message.answer("Язык группы установлен на русский!")
    else:
        await message.answer("Invalid language. Use /setgrouplang en or /setgrouplang ru.")

# Команда для выбора языка в личных сообщениях
@router.message(Command("language"))
async def cmd_language(message: Message):
    if message.chat.type != "private":
        await message.answer("This command is only available in private chats.")
        return

    user_languages[str(message.from_user.id)] = "choose"
    await message.answer("Choose language:\n1. English\n2. Russian")


# Команды
@router.message(Command("start"))
async def cmd_start(message: Message):
    lang_code = get_language(message.chat.id, message.chat.type)
    current_language = load_language(lang_code)
    await message.answer("\n".join(current_language["start"]), parse_mode="HTML")

@router.message(Command("info"))
async def cmd_info(message: Message):
    lang_code = get_language(message.chat.id, message.chat.type)
    current_language = load_language(lang_code)
    await message.answer("\n".join(current_language["info"]), parse_mode="HTML")

@router.message(Command("donate"))
async def cmd_info(message: Message):
    lang_code = get_language(message.chat.id, message.chat.type)
    current_language = load_language(lang_code)
    await message.answer("\n".join(current_language["donate"]), parse_mode="HTML")

@router.message(Command("contacts"))
async def cmd_info(message: Message):
    lang_code = get_language(message.chat.id, message.chat.type)
    current_language = load_language(lang_code)
    await message.answer("\n".join(current_language["contacts"]), parse_mode="HTML")

@router.message(Command("contract"))
async def cmd_info(message: Message):
    lang_code = get_language(message.chat.id, message.chat.type)
    current_language = load_language(lang_code)
    await message.answer("\n".join(current_language["contract"]), parse_mode="HTML")


@router.message(Command("buy"))
async def cmd_info(message: Message):
    lang_code = get_language(message.chat.id, message.chat.type)
    current_language = load_language(lang_code)
    await message.answer("\n".join(current_language["buy"]), parse_mode="HTML")

@router.message(Command("price"))
async def cmd_price(message: Message):
    lang_code = get_language(message.chat.id, message.chat.type)
    current_language = load_language(lang_code)

    data = await get_token_data()
    if data:
        pairs = data.get("pairs", [])
        logging.info(f"API response pairs: {pairs}")  # Логируем данные пар
        if pairs:
            pair = pairs[0]
            price = pair.get("priceUsd", "N/A")
            price_change_hour = pair.get("priceChange", {}).get("h1", "N/A")
            price_change_day = pair.get("priceChange", {}).get("h24", "N/A")
            volume = pair.get("volume", {}).get("h24", "N/A")
            liquidity_usd = pair.get("liquidity", {}).get("usd", "N/A")

            volume = format_number(volume)
            liquidity_usd = format_number(liquidity_usd)

            # Форматируем изменения цены
            def format_change(change):
                if change == "N/A":
                    return "N/A"
                try:
                    change_float = float(change)
                    arrow = "🟢" if change_float > 0 else "🔴" if change_float < 0 else "⚪"
                    return f"{arrow} {abs(change_float)}%"
                except ValueError:
                    logging.error(f"Error processing change: {change}")
                    return "Invalid Data"

            price_change_hour = format_change(price_change_hour)
            price_change_day = format_change(price_change_day)

            try:
                await message.answer(
                    "\n".join([
                        current_language["token_info"]["title"],
                        "",
                        current_language["token_info"]["price"].format(price=price),
                        "",
                        current_language["token_info"]["price_changes"]["title"],
                        current_language["token_info"]["price_changes"]["hour"].format(
                            price_change_hour=price_change_hour),
                        current_language["token_info"]["price_changes"]["day"].format(
                            price_change_day=price_change_day),
                        "",
                        current_language["token_info"]["volume"].format(volume=volume),
                        current_language["token_info"]["liquidity"].format(liquidity_usd=liquidity_usd)
                    ]),
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Error sending message: {e}")
        else:
            logging.error("No pairs found in the API response.")
            await message.answer(current_language["token_info"]["unavailable_data"])
    else:
        logging.error("Failed to fetch data from API.")
        await message.answer(current_language["token_info"]["fetch_error"])



# Обработка выбора языка
@router.message()
async def handle_user_input(message: Message):
    user_id = str(message.from_user.id)
    if user_languages.get(user_id) == "choose":
        user_input = message.text.strip()
        if user_input == "1":
            user_languages[user_id] = "en"
            save_user_languages()
            await message.answer("Language set to English!")
        elif user_input == "2":
            user_languages[user_id] = "ru"
            save_user_languages()
            await message.answer("Язык установлен на русский!")
        else:
            await message.answer("Invalid choice. Please send 1 for English or 2 for Russian.")



# Подключение маршрутизатора
dp.include_router(router)

# Запуск бота
async def main():
    logging.info("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
