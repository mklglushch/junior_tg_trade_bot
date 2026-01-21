import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")


# 🔹 FSM States
# =========================
class TradeForm(StatesGroup):
    exchange = State()
    asset = State()
    bank = State()
    buy_price = State()
    sell_price = State()
    amount_usdt = State()
    fee_percent = State()


# =========================
# 🔹 Business Logic
# =========================
def calculate_trade(buy: float, sell: float, amount: float, fee_percent: float):
    spread_percent = (sell - buy) / sell * 100
    net_percent = spread_percent - fee_percent

    profit = (sell - buy) * amount * (1 - fee_percent / 100)
    total_fee = (sell - buy) * amount * (fee_percent / 100)

    return {
        "spread_percent": spread_percent,
        "net_percent": net_percent,
        "total_fee": total_fee,
        "profit": profit
    }


# =========================
# 🔹 Handlers
# =========================

async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введи біржу:")
    await state.set_state(TradeForm.exchange)


async def exchange_select(message: Message, state: FSMContext):
    await state.update_data(exchange=message.text)
    await message.answer("Введи актив:")
    await state.set_state(TradeForm.asset)

    
async def asset_select(message: Message, state: FSMContext):
    await state.update_data(asset=message.text)
    await message.answer("Введи банк:")
    await state.set_state(TradeForm.bank)

async def bank_select(message: Message, state: FSMContext):
    await state.update_data(bank=message.text)
    await message.answer("Введи **ціну купівлі**:")
    await state.set_state(TradeForm.buy_price)


async def buy_price_handler(message: Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(buy_price=value)
    await message.answer("Введи **ціну продажу**:")
    await state.set_state(TradeForm.sell_price)


async def sell_price_handler(message: Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(sell_price=value)
    await message.answer("Введи **кількість USDT**:")
    await state.set_state(TradeForm.amount_usdt)


async def amount_handler(message: Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(amount_usdt=value)
    await message.answer("Введи **комісію (%)**:")
    await state.set_state(TradeForm.fee_percent)


async def fee_handler(message: Message, state: FSMContext):
    try:
        fee_percent = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(fee_percent=fee_percent)
    data = await state.get_data()

    result = calculate_trade(
        buy=data["buy_price"],
        sell=data["sell_price"],
        amount=data["amount_usdt"],
        fee_percent=fee_percent

    )

    await message.answer(
        f"📊 **Результат:**\n"
        f"Біржа: {data['exchange']}\n"
        f"Актив: {data['asset']}\n"
        f"Банк: {data['bank']}\n"
        f"Купівля: {data['buy_price']}\n"
        f"Продаж: {data['sell_price']}\n"
        f"USDT: {data['amount_usdt']}\n"
        f"Комісія: {fee_percent}%\n\n"
        f"Спред: {result['spread_percent']:.2f}%\n"
        f"Чистий відсоток: {result['net_percent']:.2f}%\n"
        f"💰 Профіт: {result['profit']:.2f} USDT"
    )


    await state.clear()


# =========================
# 🔹 TEST COMMAND
# =========================
async def test_handler(message: Message):
    buy = 44.36
    sell = 44.5
    amount = 195
    fee_percent = 0.4

    result = calculate_trade(buy, sell, amount, fee_percent)

    await message.answer(
        f"🧪 **TEST MODE**\n"
        f"Купівля: {buy}\n"
        f"Продаж: {sell}\n"
        f"USDT: {amount}\n"
        f"Комісія: {fee_percent}%\n\n"
        f"Комісія: {result['total_fee']:.2f} USDT\n"
        f"Спред: {result['spread_percent']:.2f}%\n"
        f"Чистий відсоток: {result['net_percent']:.2f}\n"
        f"Профіт: {result['profit']:.2f}"
        )


# =========================
# 🚀 Bot Start
# =========================
async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="Markdown")
    )
    dp = Dispatcher()

    dp.message.register(start_handler, Command("start"))
    dp.message.register(test_handler, Command("test"))

    dp.message.register(exchange_select, TradeForm.exchange)
    dp.message.register(asset_select, TradeForm.asset)
    dp.message.register(bank_select, TradeForm.bank)
    dp.message.register(buy_price_handler, TradeForm.buy_price)
    dp.message.register(sell_price_handler, TradeForm.sell_price)
    dp.message.register(amount_handler, TradeForm.amount_usdt)
    dp.message.register(fee_handler, TradeForm.fee_percent)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())