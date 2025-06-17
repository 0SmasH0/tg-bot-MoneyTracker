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
    orm_check_wallet_relationship, orm_get_category_transaction, orm_get_wallet_transfer, orm_get_user_budget, \
    orm_get_user_category, get_all_periods, orm_add_budget, orm_get_category_transaction_for_budget, get_period_id, \
    orm_delete_user_budget, orm_check_budget_limit, orm_update_budget_limit
from function.date import day_week_year

from function.work_with_excel import data_in_excel
from keyboards import reply,inline_kb
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_kb import inline_profile, dynamics_inline_kb_options, dynamics_inline_kb_wallet_name_id, \
    dynamics_inline_kb_money, dynamics_inline_kb_period_name_id

recurring_payment_router = Router()


class RecurringPayment(StatesGroup):
    rp_name_expenses = State()
    option = State()
    rp_period_expenses = State()
    rp_amount_expenses = State()
    add_rp_name_expenses = State()
    add_rp_amount_expenses = State()

@recurring_payment_router.message(StateFilter('*'), F.text.contains('Добавить регулярный платёж'))
async def recurring_payment(message: Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    tr = await state.get_data()

    exp_user_cat = await orm_get_user_category(session, {'user_id': user_id, 'category_type_name': 'Расход'})

    user_cat = {(i.category_name, i.category_id) for i in exp_user_cat}

    info_b = await orm_get_user_budget(session, message.from_user.id, tr['budget_period_expenses'][1])

    bud_cat = {(i[1], i[0].category_id) for i in info_b}

    cat = user_cat - bud_cat
    if cat:
        text_profile = (
                    f'Выберите категорию, которую хотите добавить в бюджет:'
                )
        inline_kb_cat = inline_kb.dynamics_inline_kb_budget_name_id(list(cat))

        await message.answer(text_profile,
                             reply_markup=inline_kb_cat.as_markup(resize_keyboard=True))

        await state.set_state(RecurringPayment.add_rp_name_expenses)
    else:
        text_profile = (
                    f'У вас нету категорий для этого периода,которые бы не были задействованы.\n\n'
                    f'Создайте новую категорию'
                )
        await message.answer(text_profile)


@recurring_payment_router.message(F.text == 'Регулярные платежи 📅')
async def recurring_payment(message: Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    user_budget = await orm_get_user_budget(session, user_id)
    data = day_week_year()

    if user_budget:
        periods = await get_all_periods(session)

        budget_info = {period[0].period_name: [] for period in periods}
        for ub in user_budget:
            key = ub[2]

            try:
                match key:
                    case "День":
                        print('-------------------------', data['День'])
                        f = await orm_get_category_transaction_for_budget(session, message.from_user.id, ub[1], data['День'])
                        print('111111',f)
                        amount = sum([i[0].amount for i in f])
                        value = f'— {ub[1]}: {amount} / {ub[0].budget_limit} {"⚠ превышен" if amount > ub[0].budget_limit else ""}'
                    case "Месяц":
                        print('-------------------------', data['Месяц'])
                        f = await orm_get_category_transaction_for_budget(session, message.from_user.id, ub[1], data['Месяц'])
                        print('2222222',f)
                        amount = sum([i[0].amount for i in f])
                        value = f'— {ub[1]}: {amount} / {ub[0].budget_limit} {"⚠ превышен" if amount > ub[0].budget_limit else ""}'
                    case "Год":
                        f = await orm_get_category_transaction_for_budget(session, message.from_user.id, ub[1], data['Год'])
                        amount = sum([i[0].amount for i in f])
                        value = f'— {ub[1]}: {amount} / {ub[0].budget_limit} {"⚠ превышен" if amount > ub[0].budget_limit else ""}'

            except AttributeError as e:
                continue

            budget_info[key].append(value)


        budget_info_1 = "\n".join([wallet for wallet in budget_info["День"]] if budget_info["День"] else [
            "Вы не создали ни одного бюджета для дня"])
        budget_info_2 = "\n".join([wallet for wallet in budget_info["Месяц"]] if budget_info["Месяц"] else [
            "Вы не создали ни одного бюджета для месяца"])
        budget_info_3 = "\n".join(
            [wallet for wallet in budget_info["Год"]] if budget_info["Год"] else ['Вы не создали ни одного бюджета для года'])

        text_profile = (
            f'<b>📅 День</b>:\n{budget_info_1}\n\n'
            f'<b>📅 Месяц</b>:\n{budget_info_2}\n\n'
            f'<b>📅 Год</b>:\n{budget_info_3}\n'
        )

    else:
        text_profile = (
            f'💡 У вас пока не создано ни одного бюджета.\n\n'
            f'Бюджет — это лимит на расходы в выбранной категории и периоде.\n'
            f'Создайте первый, чтобы контролировать свои финансы!'

        )

    await message.answer(text_profile, reply_markup=reply.budget_kb_administration.as_markup(resize_keyboard=True))
    await state.set_state(RecurringPayment.rp_period_expenses)

# @recurring_payment_router.message(RecurringPayment.budget_period_expenses, lambda c: c.text in ['День','Месяц', 'Год'])
# async def recurring_payment(message: Message, session: AsyncSession, state: FSMContext):
#
#     period_id = await get_period_id(session, message.text)
#     user_id = message.from_user.id
#
#     await state.update_data(budget_period_expenses=(message.text, period_id))
#
#     info_b = await orm_get_user_budget(session, user_id, period_id)
#
#     bud_cat = [(i[1],i[0].category_id) for i in info_b]
#
#     await message.answer('f',
#                          reply_markup=reply.budget_main_btn.as_markup(resize_keyboard=True))
#
#     if bud_cat:
#         inline_kb_st = inline_kb.dynamics_inline_kb_budget_name_id(bud_cat)
#         await message.answer(
#             f'Выберите бюджет, который хотите редактировать:',
#             reply_markup=inline_kb_st.as_markup(resize_keyboard=True))
#     else:
#         await message.answer(
#             f'У вас не создано ни одного бюджета')
#
#
#     await state.set_state(RecurringPayment.budget_name_expenses)
#
#
# @recurring_payment_router.callback_query(RecurringPayment.budget_name_expenses, F.data)
# async def profile_1(callback: types.CallbackQuery, session: AsyncSession,state: FSMContext):
#
#     category_name, category_id = ast.literal_eval(callback.data)
#
#     await state.update_data(budget_name_expenses=(category_name, category_id))
#
#     text = f'Выберите, что хотите изменить в <b>{category_name}</b>:'
#
#     options = ['Изменить сумму лимита', 'Удалить бюджет']
#
#     inline_kb = dynamics_inline_kb_options(options)
#
#     await callback.message.edit_text(text, reply_markup=inline_kb.as_markup(resize_keyboard=True))
#
#     await state.set_state(RecurringPayment.option)
#
# @recurring_payment_router.callback_query(RecurringPayment.option, F.data)
# async def profile_1(callback: types.CallbackQuery, session: AsyncSession,state: FSMContext):
#     await callback.message.delete()
#     await state.update_data(option=callback.data)
#
#     tr = await state.get_data()
#
#     if callback.data == f"Удалить бюджет":
#         text = (
#                 f'Бюджет успешно удалён!!!'
#             )
#
#         await orm_delete_user_budget(session, callback.from_user.id,tr['budget_period_expenses'][1], tr['budget_name_expenses'][1])
#         user_id = callback.from_user.id
#
#         info_b = await orm_get_user_budget(session, user_id, callback.from_user.id,tr['budget_period_expenses'][1])
#
#         bud_cat = [(i[1], i[0].category_id) for i in info_b]
#
#         await callback.message.answer('f',
#                              reply_markup=reply.budget_main_btn.as_markup(resize_keyboard=True))
#
#         if bud_cat:
#             inline_kb_st = inline_kb.dynamics_inline_kb_budget_name_id(bud_cat)
#             await callback.message.answer(
#                 f'Выберите бюджет, который хотите редактировать:',
#                 reply_markup=inline_kb_st.as_markup(resize_keyboard=True))
#         else:
#             await callback.message.answer(
#                 f'У вас не создано ни одного бюджета')
#
#         return
#
#     else:
#         text = (
#                     f'Вы выбрали функцию: <b>{callback.data}</b>\n\n'
#                     f'Введите изменённый параметр:'
#             )
#
#     await callback.message.answer(text)
#
#     await state.set_state(RecurringPayment.budget_amount_expenses)
#
# @recurring_payment_router.message(RecurringPayment.budget_amount_expenses, F.text)
# async def profile_122(message: Message, session: AsyncSession, state: FSMContext):
#     text = 'Изменение сделано успешно'
#
#     tr = await state.get_data()
#
#     match tr['option']:
#         case 'Изменить название':
#             if message.text == tr['wallet_name']:
#                 text = (
#                         f'Ваш{"" if tr['wallet_type'] != "Цель" else "а"} {tr["wallet_type"]} имеет такое же название\n\n'
#                         f'Для изменения напишите другое название:'
#                 )
#                 await message.answer(text)
#                 return
#             else:
#                 data['wallet_name'] = message.text
#                 data['user_id'] = message.from_user.id
#                 data['wallet_type_name'] = tr['wallet_type']
#                 check = await orm_check_unique_wallet_name(session, data)
#                 if check:
#                     text = (
#                             f'У вас уже есть {tr["wallet_type"]} c таким названием\n\n'
#                             f'Напишите другое название:'
#                     )
#                     await message.answer(text)
#                     return
#                 else:
#                     await orm_update_wallet_name(session, data)
#
#         case 'Изменить сумму лимита':
#             data = {'user_id': message.from_user.id, "period_id": tr['budget_period_expenses'][1], "category_id": tr['budget_name_expenses'][1]}
#             amount = await orm_check_budget_limit(session, data)
#
#             if float(message.text) == amount:
#                 text = (
#                         f'Текущий бюджет имеет ту же сумму лимита\n\n'
#                         f'Для изменения напишите другую сумму:'
#                 )
#                 await message.answer(text)
#                 return
#             else:
#                 data['budget_limit'] = float(message.text)
#                 await orm_update_budget_limit(session, data)
#
#             await message.answer(text)
#             info_b = await orm_get_user_budget(session, message.from_user.id, tr['budget_period_expenses'][1])
#
#             bud_cat = [(i[1], i[0].category_id) for i in info_b]
#
#             await message.answer('f',
#                                           reply_markup=reply.budget_main_btn.as_markup(resize_keyboard=True))
#
#             if bud_cat:
#                 inline_kb_st = inline_kb.dynamics_inline_kb_budget_name_id(bud_cat)
#                 await message.answer(
#                     f'Выберите бюджет, который хотите редактировать:',
#                     reply_markup=inline_kb_st.as_markup(resize_keyboard=True))
#             await state.set_state(RecurringPayment.budget_name_expenses)
#
#
# @recurring_payment_router.callback_query(RecurringPayment.add_budget_name_expenses, F.data)
# async def recurring_payment(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
#
#     name_exp = ast.literal_eval(callback.data)
#     await state.update_data(add_budget_name_expenses=name_exp)
#
#
#     text_profile = (
#                 f'Выбранная категория: <b>{name_exp[0]}</b>\n\n'
#                 f'Напишите сумму лимита:'
#             )
#
#     await callback.message.edit_text(text_profile)
#
#     await state.set_state(RecurringPayment.add_budget_amount_expenses)
#
#
# @recurring_payment_router.message(recurring_payment.add_budget_amount_expenses, F.text)
# async def recurring_payment(message: Message, session: AsyncSession, state: FSMContext):
#
#     if message.text.isdigit():
#
#         await state.update_data(add_budget_amount_expenses=float(message.text))
#
#         data = await state.get_data()
#         user_id = message.from_user.id
#         await orm_add_budget(session, user_id, data)
#
#         text_profile = f'Бюджет успешно добавлен!!!'
#     else:
#         text_profile = (
#             f'Вы ввели сумму лимита неверно!!!\n\n'
#             f'Введите сумму заново'
#         )
#
#         await state.set_state(RecurringPayment.add_budget_amount_expenses)
#
#     await message.answer(text_profile, reply_markup=reply.budget_main_btn.as_markup(resize_keyboard=True))