import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================
# 🔹 FSM States
# =========================
class TradeForm(StatesGroup):
    exchange = State()
    asset = State()
    bank = State()
    buy_price = State()
    sell_price = State()
    amount = State()
    fee = State()


# =========================
# 🔹 Business Logic
# =========================
def calculate_trade(buy: float, sell: float, amount: float, fee: float):
    spread = sell - buy                          # спред за 1 одиницю активу (грн)
    spread_percent = spread / buy * 100          # спред у відсотках

    spent = buy * amount                         # витрачено грн на купівлю
    real_amount = amount - fee                   # реально активу після комісії
    received = sell * real_amount                # отримано грн з продажу

    profit = received - spent                    # чистий прибуток (грн)
    net_percent = profit / spent * 100           # чистий відсоток
    fee_grn = fee * sell                         # комісія у грн (за курсом продажу)

    return {
        "spread": spread,
        "spread_percent": spread_percent,
        "real_amount": real_amount,
        "fee_grn": fee_grn,
        "profit": profit,
        "net_percent": net_percent,
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
    await message.answer("Введи *ціну купівлі*:")
    await state.set_state(TradeForm.buy_price)


async def buy_price_handler(message: Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(buy_price=value)
    await message.answer("Введи *ціну продажу*:")
    await state.set_state(TradeForm.sell_price)


async def sell_price_handler(message: Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(sell_price=value)
    data = await state.get_data()
    asset = data.get("asset", "активу")
    await message.answer(f"Введи *кількість {asset}*:")
    await state.set_state(TradeForm.amount)


async def amount_handler(message: Message, state: FSMContext):
    try:
        value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(amount=value)
    data = await state.get_data()
    asset = data.get("asset", "активу")
    await message.answer(f"Введи *комісію ({asset})*:")
    await state.set_state(TradeForm.fee)


async def fee_handler(message: Message, state: FSMContext):
    try:
        fee = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введи число")
        return

    await state.update_data(fee=fee)
    data = await state.get_data()
    asset = data.get("asset", "активу")

    result = calculate_trade(
        buy=data["buy_price"],
        sell=data["sell_price"],
        amount=data["amount"],
        fee=fee,
    )

    await message.answer(
        f"📊 *Результат:*\n"
        f"Біржа: {data['exchange']}\n"
        f"Актив: {data['asset']}\n"
        f"Банк: {data['bank']}\n"
        f"Купівля: {data['buy_price']}\n"
        f"Продаж: {data['sell_price']}\n"
        f"{asset}: {data['amount']}\n"
        f"Комісія: {fee} {asset}\n\n"
        f"Спред: {result['spread']:.2f} грн/{asset} ({result['spread_percent']:.2f}%)\n"
        f"Реально {asset}: {result['real_amount']:.2f}\n"
        f"Комісія: {result['fee_grn']:.2f} грн\n"
        f"Чистий відсоток: {result['net_percent']:.2f}%\n"
        f"💰 Профіт: {result['profit']:.2f} грн"
    )

    await state.clear()


# =========================
# 🔹 TEST COMMAND
# =========================
async def test_handler(message: Message):
    buy = 45.64
    sell = 46.22
    amount = 65.79
    fee = 0.21
    asset = "USDT"

    result = calculate_trade(buy, sell, amount, fee)

    await message.answer(
        f"🧪 *TEST MODE*\n"
        f"Купівля: {buy}\n"
        f"Продаж: {sell}\n"
        f"{asset}: {amount}\n"
        f"Комісія: {fee} {asset}\n\n"
        f"Спред: {result['spread']:.2f} грн/{asset} ({result['spread_percent']:.2f}%)\n"
        f"Реально {asset}: {result['real_amount']:.2f}\n"
        f"Комісія: {result['fee_grn']:.2f} грн\n"
        f"Чистий відсоток: {result['net_percent']:.2f}%\n"
        f"💰 Профіт: {result['profit']:.2f} грн"
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
    dp.message.register(amount_handler, TradeForm.amount)
    dp.message.register(fee_handler, TradeForm.fee)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())