import ast
from datetime import datetime

from aiogram import types, Router, F, Bot
from aiogram.exceptions import TelegramBadRequest

from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile, BufferedInputFile
from aiogram.utils.formatting import as_list, as_marked_section, Bold, Italic, Text, as_line
from annotated_types.test_cases import cases

from database.orm_query import orm_get_user, orm_add_user, orm_wipe_user_data, orm_get_user_wallets_all, \
    orm_get_wallet_type_all, orm_add_default_categories, orm_add_default_wallet, orm_get_user_wallets, orm_add_wallet, \
    orm_get_wallet_type_id, orm_get_currency_id, orm_add_wallet_target, orm_add_wallet_investment, \
    orm_get_user_wallets_not_zero, orm_get_user_wallets_without_one, orm_add_wallet_transfer, orm_update_wallet_balance
# orm_add_default_categories, orm_get_incomes, \
    # orm_get_expenses)
from function.work_with_excel import data_in_excel
from keyboards import reply,inline_kb
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_kb import inline_profile, dynamics_inline_kb_wallet, dynamics_inline_kb_wallet_name_id, \
    dynamics_inline_kb_wallet_name_id_suma

transfer_router = Router()

class Transfer(StatesGroup):
    first_active_name = State()
    first_active_id = State()
    first_active_funds_available = State()
    second_active_name = State()
    second_active_id = State()
    transfer_suma = State()


@transfer_router.message(F.text == 'Переводы 🔁')
async def transfer_1(message: Message, session: AsyncSession, state: FSMContext):

    actives = await orm_get_user_wallets_all(session, message.from_user.id)

    if len(actives) < 2:
        text = (
            'У вас недостаточно открытых активов для перевода\n\n'
            'Для проведения перевода создайте новый кошелёк/вклад/цель'
        )

        await message.answer(text, reply_markup=reply.start_kb.as_markup(resize_keyboard=True))
        return

    foo = await orm_get_user_wallets_not_zero(session, message.from_user.id)

    if len(foo) == 0:
        text = (
            'У вас недостаточно средств в активах для перевода\n\n'
            'Для проведения перевода пополните кошелёк/вклад/цель'
        )

        await message.answer(text, reply_markup=reply.start_kb.as_markup(resize_keyboard=True))
        return

    text = 'Пожалуйста, выберите актив, с которого хотите выполнить перевод (кошелёк, вклад или цель):'


    inline_kb = dynamics_inline_kb_wallet_name_id_suma(foo)

    await message.answer('fff', reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await message.answer(text, reply_markup=inline_kb.as_markup(resize_keyboard=True))
    await state.set_state(Transfer.first_active_name)


@transfer_router.callback_query(Transfer.first_active_name, F.data)
async def transfer_2(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    active_name, active_id, active_balance = ast.literal_eval(callback.data)

    await state.update_data(first_active_name=active_name)
    await state.update_data(first_active_id=active_id)
    await state.update_data(first_active_funds_available=active_balance)

    await callback.message.delete()
    preview = (
                f'<b>Перевод из актива</b>: {active_name} ({active_balance})\n\n'
                f'<b>Выберите актив куда нужно перевести:</b>'
    )

    data = {'user_id': callback.from_user.id, 'wallet_id': int(active_id)}

    foo = await orm_get_user_wallets_without_one(session, data)

    # w_tr = await orm_get_user_wallets_target(session, data)
    # name_tr_list = [i.wallet_name for i in w_tr]
    #
    # res = []
    #
    # for i in foo:
    #     if i.wallet_name not in name_tr_list:
    #         res.append(i)

    inline_kb = dynamics_inline_kb_wallet_name_id(foo)

    await callback.message.answer(preview, reply_markup=inline_kb.as_markup(resize_keyboard=True))

    await state.set_state(Transfer.second_active_name)

@transfer_router.callback_query(Transfer.second_active_name, F.data)
async def transfer_3(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    active_name, active_id = ast.literal_eval(callback.data)

    await state.update_data(second_active_name=active_name)
    await state.update_data(second_active_id=active_id)


    await callback.message.delete()

    tr = await state.get_data()

    preview = (
                f'<b>Перевод из актива</b>: {tr["first_active_name"]} ({tr['first_active_funds_available']})\n\n'
                f'<b>Перевод в актив: {active_name}</b>\n\n'
                f'Напишите сумму,которую хотите перевести:'
    )

    await callback.message.answer(preview)

    await state.set_state(Transfer.transfer_suma)

@transfer_router.message(Transfer.transfer_suma, F.text)
async def transfer_4(message: Message, session: AsyncSession, state: FSMContext):
    tr = await state.get_data()

    if float(message.text) > tr['first_active_funds_available'] or float(message.text) <= 0:
        if float(message.text) > tr['first_active_funds_available']:
            text = (
                f'Невозможно произвести перевод,т.к ваша сумма больше чем та,что есть на счёте {tr['first_active_name']}\n\n'
                f'Введите сумму заново:'
            )
        else:
            text = (
                f'Невозможно произвести перевод,т.к ваша сумма меньше или равна нулю\n\n'
                f'Введите сумму заново:'
            )

        await message.answer(text)
        await state.set_state(Transfer.transfer_suma)

        return

    await state.update_data(transfer_suma=message.text)

    tr = await state.get_data()

    data = {
            'source_wallet_id': tr['first_active_id'],
            'target_wallet_id': tr['second_active_id'],
            'amount': message.text
    }

    await orm_add_wallet_transfer(session, data)

    data_wallet = {
            'wallet_id': tr['second_active_id'],
            'cat_type': 'Доход',
            'suma': tr['transfer_suma']
    }

    await orm_update_wallet_balance(session, data_wallet)

    data_wallet["cat_type"] = "Расход"
    data_wallet["wallet_id"] = tr['first_active_id']

    await orm_update_wallet_balance(session, data_wallet)

    text = f'Перевод прошёл успешно'

    await message.answer(text)
