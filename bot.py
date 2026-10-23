"""Telegram-бот студии KARMIN: приём заявок на проекты и вопросов."""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8017286747"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

dp = Dispatcher()


class Form(StatesGroup):
    project = State()
    question = State()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Заказать проект", callback_data="project")],
        [InlineKeyboardButton(text="💬 Задать вопрос", callback_data="question")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ Отмена", callback_data="cancel")],
    ])


WELCOME = (
    "🔴 <b>Привет! Это KARMIN, студия цифровых миров.</b>\n\n"
    "Мы делаем сайты с 3D-анимацией и дизайном, который запоминается.\n\n"
    "Опишите свой проект или задайте вопрос, и мы скоро ответим. "
    "Выберите, что вам нужно 👇"
)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu())


@dp.callback_query(F.data == "project")
async def ask_project(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.project)
    await cb.message.answer(
        "🚀 <b>Расскажите о проекте</b>\n\n"
        "Что нужно сделать, для кого, какие сроки и бюджет, есть ли примеры, "
        "которые нравятся. Напишите всё одним сообщением.",
        reply_markup=cancel_kb(),
    )
    await cb.answer()


@dp.callback_query(F.data == "question")
async def ask_question(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.question)
    await cb.message.answer(
        "💬 <b>Задайте ваш вопрос</b>\n\nНапишите его одним сообщением.",
        reply_markup=cancel_kb(),
    )
    await cb.answer()


@dp.callback_query(F.data == "cancel")
async def cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.answer("Хорошо, отменили. Чем ещё помочь?", reply_markup=main_menu())
    await cb.answer()


def user_info(message: Message) -> str:
    u = message.from_user
    name = u.full_name
    username = f"@{u.username}" if u.username else "без username"
    return f"От: <a href=\"tg://user?id={u.id}\">{name}</a> ({username}, id <code>{u.id}</code>)"


async def forward_to_admin(message: Message, bot: Bot, header: str) -> None:
    # Сначала короткое сообщение-метка, затем сама заявка пользователя
    await bot.send_message(ADMIN_ID, header)
    await bot.send_message(ADMIN_ID, user_info(message))
    await bot.copy_message(ADMIN_ID, message.chat.id, message.message_id)


@dp.message(StateFilter(Form.project))
async def got_project(message: Message, state: FSMContext, bot: Bot) -> None:
    await forward_to_admin(message, bot, "<b>ПРОЕКТ!</b>")
    await state.clear()
    await message.answer(
        "✅ Спасибо! Заявка отправлена, мы свяжемся с вами в ближайшее время.",
        reply_markup=main_menu(),
    )


@dp.message(StateFilter(Form.question))
async def got_question(message: Message, state: FSMContext, bot: Bot) -> None:
    await forward_to_admin(message, bot, "<b>ВОПРОС!</b>")
    await state.clear()
    await message.answer(
        "✅ Вопрос отправлен! Скоро ответим.",
        reply_markup=main_menu(),
    )


@dp.message()
async def fallback(message: Message) -> None:
    await message.answer("Выберите, что вам нужно 👇", reply_markup=main_menu())


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("Не найден BOT_TOKEN. Проверьте файл .env")
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Канал постит через тот же токен, поэтому удаляем вебхук и пропускаем старые апдейты
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот KARMIN запущен")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
