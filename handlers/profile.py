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
from pyexpat.errors import messages

from database.orm_query import orm_get_user, orm_add_user, orm_wipe_user_data, orm_get_user_wallets_all, \
    orm_get_wallet_type_all, orm_add_default_categories, orm_add_default_wallet, orm_get_user_wallets, orm_add_wallet, \
    orm_get_wallet_type_id, orm_get_currency_id, orm_add_wallet_target, orm_add_wallet_investment, \
    orm_update_wallet_name, orm_check_unique_wallet_name, orm_check_wallet_target, \
    orm_update_wallet_target_amount, orm_check_wallet_investment, \
    orm_update_wallet_investment, orm_delete_wallet, orm_wallet_restore, orm_get_user_wallet, \
    orm_check_wallet_relationship, orm_get_category_transaction, orm_get_wallet_transfer
# orm_add_default_categories, orm_get_incomes, \
    # orm_get_expenses)
from function.work_with_excel import data_in_excel
from keyboards import reply,inline_kb
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_kb import inline_profile, dynamics_inline_kb_options, dynamics_inline_kb_wallet_name_id

profile_router = Router()


@profile_router.message(F.text == 'Профиль 👤')
async def profile(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    user = await orm_get_user(session, user_id)

    text_profile = (
                f'Профиль пользователя: <b>{user.username}</b>'
            )

    await message.answer(text_profile,
                         reply_markup=inline_profile.as_markup(resize_keyboard=True))


@profile_router.callback_query(lambda c: c.data in ['drop_data_user','history'])
async def profile_del(callback: CallbackQuery, session: AsyncSession):
    data = callback.data
    user_id = int(callback.from_user.id)

    match data:

        case 'drop_data_user':

            await orm_wipe_user_data(session, user_id)
            # await orm_add_default_categories(session,user_id)
            user = await orm_get_user(session, user_id)
            await orm_add_default_categories(session, user_id)


            await orm_add_default_wallet(session, user_id)

            text_profile = (
                f'Профиль пользователя: <b>{user.username}</b>'
            )

            new_markup = inline_profile.as_markup(resize_keyboard=True)
            try:
                await callback.message.edit_text(text_profile, reply_markup=new_markup)
                await callback.answer("Данные успешно очистились", show_alert=False)
            except TelegramBadRequest as e:
                await callback.answer("Данные успешно очистились", show_alert=False)

        case 'history':

            transfer = await orm_get_wallet_transfer(session, user_id)

            incomes = await orm_get_category_transaction(session, user_id, 'Доход')

            for i in incomes:
                print('------------',i[0])

            expenses = await orm_get_category_transaction(session, user_id, 'Расход')

            xlsx_bytes = data_in_excel(incomes, expenses, transfer)

            if incomes or expenses:
                hart_file = BufferedInputFile(xlsx_bytes.read(), filename='Доходы_и_Расходы.xlsx')

                await callback.message.answer_document(document=hart_file)

            else:
                await callback.answer('Вы не провели ни одной операции', show_alert=False)


        case _:
            pass