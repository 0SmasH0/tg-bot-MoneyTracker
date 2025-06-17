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
    orm_check_wallet_relationship
# orm_add_default_categories, orm_get_incomes, \
    # orm_get_expenses)
from function.work_with_excel import data_in_excel
from keyboards import reply,inline_kb
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.inline_kb import inline_profile, dynamics_inline_kb_options, dynamics_inline_kb_wallet_name_id

account_router = Router()


@account_router.message(F.text == 'Счета 💼')
async def profile(message: Message, session: AsyncSession,state: FSMContext):
    user_id = message.from_user.id

    wallets_types = await orm_get_wallet_type_all(session)
    wallets_info = {type.wallet_type_name: [] for type in wallets_types}

    wallets = await orm_get_user_wallets_all(session, user_id)

    suma_wallet_all, suma_wallet, suma_vklad, suma_goal = 0, 0, 0, 0

    for wallet in wallets:
        key = wallet.wallet_type.wallet_type_name

        try:
            match key:
                case "Кошелёк":
                    value = f'— {wallet.wallet_name}: {wallet.balance} {wallet.currency.currency_code}'
                    suma_wallet += wallet.balance
                case "Вклад":
                    value = f'— {wallet.wallet_name}: {wallet.balance} {wallet.currency.currency_code}\n({wallet.wallet_investment.interest_rate} %, {wallet.wallet_investment.start_date.strftime("%d.%m.%Y")}-{wallet.wallet_investment.end_date.strftime("%d.%m.%Y")})'
                    suma_vklad += wallet.balance
                case "Цель":
                    value = f'— {wallet.wallet_name}: {wallet.balance} / {wallet.wallet_target.target_amount} {wallet.currency.currency_code}'
                    suma_goal += wallet.balance

            suma_wallet_all += wallet.balance
        except AttributeError as e:
            continue

        wallets_info[key].append(value)

    wallets_info_1 = "\n".join([wallet for wallet in wallets_info["Кошелёк"]] if wallets_info["Кошелёк"] else ["Вы не создали ни одного кошелька"])
    wallets_info_2 = "\n".join([wallet for wallet in wallets_info["Вклад"]] if wallets_info["Вклад"] else ["Вы не создали ни одного вклада"])
    wallets_info_3 = "\n".join([wallet for wallet in wallets_info["Цель"]] if wallets_info["Цель"] else ["Вы не создали ни одной цели"])


    text_profile = (
                f'<b>💳 Кошельки</b>:\n{wallets_info_1}\n'
                f'<b>Итого</b>: {suma_wallet} BYN\n\n'
                f'<b>🏦 Вклады</b>:\n{wallets_info_2}\n'
                f'<b>Итого</b>: {suma_vklad} BYN\n\n'
                f'<b>🎯 Цели</b>:\n{wallets_info_3}\n'
                f'<b>Итого</b>: {suma_goal} BYN\n\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'💰 <b>Общий баланс</b>: {suma_wallet_all} BYN'
            )

    await message.answer(text_profile, reply_markup=reply.profile_kb_administration.as_markup(resize_keyboard=True))
    await state.set_state(Profile.wallet_type)



class Profile(StatesGroup):
    wallet_type = State()
    wallet_name = State()
    wallet_id = State()
    option = State()
    parameter = State()
    new_storage_name = State()
    params_storage = State()

@account_router.message(StateFilter('*'), F.text.lower().contains('создать'))
async def profile_12(message: Message, state: FSMContext):
    data = await state.get_data()
    text = f'Напишите название нового {data['wallet_type']}'
    await message.answer(text, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await state.set_state(Profile.new_storage_name)

@account_router.message(Profile.new_storage_name, F.text)
async def profile_13(message: Message, session: AsyncSession,state: FSMContext):
    data = await state.get_data()

    data_w = {
                'wallet_name': message.text,
                'user_id': message.from_user.id,
                'wallet_type_name': data['wallet_type']
    }

    wallet = await orm_check_unique_wallet_name(session, data_w)

    check = False

    if wallet is not None and wallet.is_deleted == False:

        text = (
            f'У вас уже есть {data["wallet_type"]} c таким названием\n\n'
            f'Напишите другое название:'
        )
        await message.answer(text)
        return
    elif wallet is None:
        pass
    elif wallet.is_deleted:
        check = True

    await state.update_data(new_storage_name=message.text)

    match data['wallet_type']:
        case "Кошелёк":
            text = f'Успешно добавлено'

            data = await state.get_data()

            storage_type_id = await orm_get_wallet_type_id(session, data['wallet_type'])
            storage_currency_id = await orm_get_currency_id(session, 'BYN')

            data_storage = {
                'user_id': message.from_user.id,
                'wallet_name': data['new_storage_name'],
                'balance': 0,
                'wallet_type_id': storage_type_id,
                'currency_id': storage_currency_id
            }

            if check:
                await orm_wallet_restore(session, data_storage)
            else:
                await orm_add_wallet(session, data_storage)

            add_storage = reply.profile_add_storage_func(data['wallet_type'])

            await message.answer(text, reply_markup=add_storage.as_markup(resize_keyboard=True))

            data_w = {"wallet_type_name": data['wallet_type'], "user_id": message.from_user.id}
            storage = await orm_get_user_wallets(session, data_w)
            inline_kb_st = inline_kb.dynamics_inline_kb_wallet_name_id(storage)
            await message.answer(
                f'Выберите {data['wallet_type'].lower()}, котор{"ый" if data['wallet_type'] != "Цель" else "ую"} хотите редактировать:',
                reply_markup=inline_kb_st.as_markup(resize_keyboard=True))

            await state.set_state(Profile.wallet_name)

        case "Вклад":
            text = (
                    f'Напишите процентную ставку, дату открытия и закрытия вклада\n\n'
                    f'Пример: 13.1,01.01.2025,11.03.2026'
            )
            await message.answer(text, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
            await state.set_state(Profile.params_storage)
        case "Цель":
            text = 'Напишите целевую сумму,которую хотите накопить'
            await message.answer(text, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
            await state.set_state(Profile.params_storage)


@account_router.message(Profile.params_storage, F.text)
async def profile_13(message: Message, session: AsyncSession, state: FSMContext):
    await state.update_data(params_storage=message.text)
    data = await state.get_data()

    text = f'Успешно добавлено'

    params = message.text.split(',')

    storage_type_id = await orm_get_wallet_type_id(session, data['wallet_type'])
    storage_currency_id = await orm_get_currency_id(session, 'BYN')

    data_storage = {
        'user_id': message.from_user.id,
        'wallet_name': data['new_storage_name'],
        'wallet_type_id': storage_type_id,
        'currency_id': storage_currency_id
    }

    if len(params) == 1:
        data_storage['balance'] = 0

        wallet_id = await orm_add_wallet(session, data_storage)
        data_storage['wallet_id'] = wallet_id
        data_storage['target_amount'] = float(params[0])

        await orm_add_wallet_target(session, data_storage)
    else:
        data_storage['interest_rate'] = float(params[0])
        data_storage['start_date'] = datetime.strptime(params[1], '%d.%m.%Y').date()
        data_storage['end_date'] = datetime.strptime(params[2], '%d.%m.%Y').date()

        wallet_id = await orm_add_wallet(session, data_storage)
        data_storage['wallet_id'] = wallet_id

        await orm_add_wallet_investment(session, data_storage)

    add_storage = reply.profile_add_storage_func(data['wallet_type'])

    await message.answer(text, reply_markup=add_storage.as_markup(resize_keyboard=True))

    data_w = {"wallet_type_name": data['wallet_type'], "user_id": message.from_user.id}
    storage = await orm_get_user_wallets(session, data_w)
    inline_kb_st = inline_kb.dynamics_inline_kb_wallet_name_id(storage)
    await message.answer(
        f'Выберите {data['wallet_type'].lower()}, котор{"ый" if data['wallet_type'] != "Цель" else "ую"} хотите редактировать:',
        reply_markup=inline_kb_st.as_markup(resize_keyboard=True))

    await state.set_state(Profile.wallet_name)


# @account_router.message(F.text == "Управление кошельками/вкладами/целями")
# async def profile_1(message: Message, state: FSMContext):
#     text = 'Выберите тип накопления, который хотите редактировать'
#
#     await message.answer(text, reply_markup=reply.profile_kb_administration.as_markup(resize_keyboard=True))
#     await state.set_state(Profile.wallet_type)

@account_router.message(Profile.wallet_type, F.text)
async def profile_1(message: Message, session: AsyncSession,state: FSMContext):

    answer = message.text

    match answer:
        case 'Кошельки':
            wallet_type = 'Кошелёк'
        case "Вклады":
            wallet_type = "Вклад"
        case "Цели":
            wallet_type = 'Цель'

    await state.update_data(wallet_type=wallet_type)

    data = {"wallet_type_name": wallet_type, "user_id": message.from_user.id}

    storage = await orm_get_user_wallets(session, data)

    add_storage = reply.profile_add_storage_func(wallet_type)
    await message.answer(
        'fff',reply_markup=add_storage.as_markup(resize_keyboard=True))

    if storage:
        inline_kb_st = inline_kb.dynamics_inline_kb_wallet_name_id(storage)
        await message.answer(
            f'Выберите {wallet_type.lower()}, котор{"ый" if wallet_type != "Цель" else "ую"} хотите редактировать:',
            reply_markup=inline_kb_st.as_markup(resize_keyboard=True))
    else:
        await message.answer(
            f'У вас не создано ни одно{'го' if answer!="Цели" else 'й'} {answer[:-1].lower()+'a' if answer!="Цели" else "цели"}')

    await state.set_state(Profile.wallet_name)

@account_router.callback_query(Profile.wallet_name, F.data)
async def profile_1(callback: types.CallbackQuery, session: AsyncSession,state: FSMContext):

    active_name, active_id = ast.literal_eval(callback.data)

    await state.update_data(wallet_name=active_name)
    await state.update_data(wallet_id=active_id)
    await callback.message.delete()
    tr = await state.get_data()

    text = f'Выберите, что хотите изменить в <b>{active_name}</b>:'

    check = await orm_check_wallet_relationship(session, active_id)

    options = ['Изменить название']

    match tr['wallet_type']:
        case 'Кошелёк':
            pass
        case "Цель":
            options.append('Изменить целевую сумму')
        case "Вклад":
            goal_options = ['Изменить процентную ставку','Изменить дату открытия вклада','Изменить дату закрытия вклада']
            options.extend(goal_options)

    if check:
        options.append(f'Деактивировать {tr['wallet_type'].lower()}')
    else:
        options.append(f'Удалить {tr['wallet_type'].lower()}')

    inline_kb = dynamics_inline_kb_options(options)

    await callback.message.answer(text, reply_markup=inline_kb.as_markup(resize_keyboard=True))

    await state.set_state(Profile.option)

@account_router.callback_query(Profile.option, F.data)
async def profile_1(callback: types.CallbackQuery, session: AsyncSession,state: FSMContext):
    await callback.message.delete()
    await state.update_data(option=callback.data)

    tr = await state.get_data()

    if callback.data == f"Удалить {tr['wallet_type'].lower()}" or callback.data == f"Деактивировать {tr['wallet_type'].lower()}":
        text = (
                f'{tr['wallet_type']} успешн{'о' if tr['wallet_type'] != "Цель" else "а"} удален{'' if tr['wallet_type'] != "Цель" else "а"}'
            )

        wal = await orm_get_user_wallet(session, tr['wallet_id'])
        if wal.balance > 0:
            text = (
                f"На счёте находится <b>{wal.balance}</b> BYN\n\n"
                f'Произведите перевод с {wal.wallet_name} на другие счета для того,чтобы удалить его'
            )

            options = ['Изменить название']

            match tr['wallet_type']:
                case 'Кошелёк':
                    pass
                case "Цель":
                    options.append('Изменить целевую сумму')
                case "Вклад":
                    goal_options = ['Изменить процентную ставку', 'Изменить дату открытия вклада',
                                    'Изменить дату закрытия вклада']
                    options.extend(goal_options)

            options.append(f'Удалить {tr['wallet_type'].lower()}')

            inline_kb = dynamics_inline_kb_options(options)

            await callback.message.answer(text, reply_markup=inline_kb.as_markup(resize_keyboard=True))

            await state.set_state(Profile.option)
            return

        await orm_delete_wallet(session, tr['wallet_id'])
        add_storage = reply.profile_add_storage_func(tr['wallet_type']) # ReplyKeyBoard ('создать вклад, ....')

        await callback.message.answer(text, reply_markup=add_storage.as_markup(resize_keyboard=True))

        data = {"wallet_type_name": tr['wallet_type'], "user_id": callback.from_user.id}

        storage = await orm_get_user_wallets(session, data) # получаем все кошельки в этом типе
        if storage:
            pass
        else:
            if tr['wallet_type'] == 'Кошелёк':
                await orm_add_default_wallet(session, callback.from_user.id)
                storage = await orm_get_user_wallets(session, data)
            else:
                match tr['wallet_type']:
                    case 'Кошелёк':
                        answer = 'Кошелька'
                    case "Цель":
                        answer = 'Цели'
                    case "Вклад":
                        answer = 'Вклада'
                await callback.message.answer(
                    f'У вас не создано ни одно{'го' if answer != "Цели" else 'й'} {answer[:-1].lower() + 'a' if answer != "Цели" else "цели"}')
                await state.set_state(Profile.wallet_name)
                return

        inline_kb_st = dynamics_inline_kb_wallet_name_id(storage)
        await callback.message.answer(
            f'Выберите {tr['wallet_type'].lower()}, котор{"ый" if tr['wallet_type'] != "Цель" else "ую"} хотите редактировать:',
            reply_markup=inline_kb_st.as_markup(resize_keyboard=True))
        await state.set_state(Profile.wallet_name)

        return
    else:
        text = (
                    f'Вы выбрали функцию: <b>{callback.data}</b>\n\n'
                    f'Введите изменённый параметр:'
            )

    await callback.message.answer(text)

    await state.set_state(Profile.parameter)


@account_router.message(Profile.parameter, F.text)
async def profile_122(message: Message, session: AsyncSession, state: FSMContext):
    text = 'Изменение сделано успешно'

    tr = await state.get_data()

    data = {'wallet_id': tr['wallet_id']}

    match tr['option']:
        case 'Изменить название':
            if message.text == tr['wallet_name']:
                text = (
                        f'Ваш{"" if tr['wallet_type'] != "Цель" else "а"} {tr["wallet_type"]} имеет такое же название\n\n'
                        f'Для изменения напишите другое название:'
                )
                await message.answer(text)
                return
            else:
                data['wallet_name'] = message.text
                data['user_id'] = message.from_user.id
                data['wallet_type_name'] = tr['wallet_type']
                check = await orm_check_unique_wallet_name(session, data)
                if check:
                    text = (
                            f'У вас уже есть {tr["wallet_type"]} c таким названием\n\n'
                            f'Напишите другое название:'
                    )
                    await message.answer(text)
                    return
                else:
                    await orm_update_wallet_name(session, data)

        case 'Изменить целевую сумму':
            amount = await orm_check_wallet_target(session, data)
            if float(message.text) == amount.target_amount:
                text = (
                        f'Текущая {tr['wallet_type']} имеет ту же итоговую сумму\n\n'
                        f'Для изменения напишите другую сумму:'
                )
                await message.answer(text)
                return
            else:
                data['target_amount'] = float(message.text)
                await orm_update_wallet_target_amount(session, data)

        case 'Изменить процентную ставку':
            rate = await orm_check_wallet_investment(session, data)
            if float(message.text) == rate.interest_rate:
                text = (
                        f'Текущий {tr['wallet_type']} имеет ту же процентную ставку\n\n'
                        f'Для изменения напишите другую процентную ставку:'
                )
                await message.answer(text)
                return
            else:
                data['interest_rate'] = float(message.text)
                data['option'] = tr['option']
                await orm_update_wallet_investment(session, data)

        case 'Изменить дату открытия вклада':
            st_date = await orm_check_wallet_investment(session, data)
            user_date = datetime.strptime(message.text, '%d.%m.%Y').date()
            if user_date== st_date.start_date:
                text = (
                        f'Текущий {tr['wallet_type']} имеет ту же дату открытия\n\n'
                        f'Для изменения напишите другую дату:'
                )
                await message.answer(text)
                return
            else:
                data['start_date'] = user_date
                data['option'] = tr['option']
                await orm_update_wallet_investment(session, data)

        case 'Изменить дату закрытия вклада':
            en_date = await orm_check_wallet_investment(session, data)
            user_date = datetime.strptime(message.text, '%d.%m.%Y').date()

            if user_date == en_date.end_date:
                text = (
                    f'Текущий {tr['wallet_type']} имеет ту же дату окончания\n\n'
                    f'Для изменения напишите другую дату:'
                )
                await message.answer(text)
                return
            else:
                data['end_date'] = user_date
                data['option'] = tr['option']
                await orm_update_wallet_investment(session, data)

    await message.answer(text)
    data = {"wallet_type_name": tr['wallet_type'], "user_id": message.from_user.id}
    storage = await orm_get_user_wallets(session, data)
    inline_kb_st = inline_kb.dynamics_inline_kb_wallet_name_id(storage)
    await message.answer(
        f'Выберите {tr['wallet_type'].lower()}, котор{"ый" if tr['wallet_type'] != "Цель" else "ую"} хотите редактировать:',
        reply_markup=inline_kb_st.as_markup(resize_keyboard=True))

    await state.set_state(Profile.wallet_name)
