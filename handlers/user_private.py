from aiogram import types, Router, F, Bot
import ast
from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile, BufferedInputFile
from aiogram.utils.formatting import as_list, as_marked_section, Bold, Italic, Text
from sqlalchemy.ext.asyncio import AsyncSession


from database.orm_query import orm_add_user, orm_get_user, orm_add_wallet, orm_add_category, \
    orm_get_user_category, orm_add_default_categories, orm_add_default_wallet, orm_get_user_wallets_all, \
    orm_update_wallet_balance, \
    orm_get_category_types_id, orm_add_category_transaction, orm_get_user_wallets, orm_delete_category, \
    orm_get_wallet_type_id
from database.orm_query_default import orm_add_default_currency, orm_add_default_category_types, \
    orm_add_default_wallet_types, orm_add_default_periods

from function.voice_detection import work_with_voice_text, voice_to_text, voice_result
from keyboards import reply, inline_kb

import io

from keyboards.inline_kb import dynamics_inline_kb_money, dynamics_inline_kb_wallet

user_private_router = Router()


@user_private_router.message(Command('start'))
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    await orm_add_default_currency(session)

    await orm_add_default_category_types(session)
    await orm_add_default_wallet_types(session)
    await orm_add_default_periods(session)

    user_id = message.from_user.id

    if await orm_get_user(session, user_id) is None:

        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        username = first_name + ' ' + last_name if last_name is not None else first_name

        data_user = {
            'user_id': user_id,
            "username": username
        }

        await orm_add_user(session, data_user)
        await orm_add_default_wallet(session, user_id)
        await orm_add_default_categories(session, user_id)
        # await orm_add_default_categories(session, user_id)


    text = as_list(Bold("Добро пожаловать в MoneyTracker!"), "\nВыберите интересующий вас пункт")
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    await message.answer(text.as_html(), reply_markup=reply.start_kb.as_markup(resize_keyboard=True))


@user_private_router.message(F.text.lower().contains('в начало'))
async def start(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()

    text = Bold('Выберите интересующий вас пункт')

    await message.answer(text.as_html(), reply_markup=reply.start_kb.as_markup(resize_keyboard=True))


@user_private_router.message(F.voice)
async def voice_message(message: Message, bot: Bot, session: AsyncSession):

    user_id = message.from_user.id
    # Получаем идентификатор файла голосового сообщения
    voice_id = message.voice.file_id

    # Получаем файл голоса
    voice_file = await bot.get_file(voice_id)
    # Загружаем содержимое файла в байткод
    file_download = await bot.download_file(voice_file.file_path)
    # Сохраняем в оперативной памяти
    voice_io = file_download
    voice_io.seek(0)

    text = voice_to_text(voice_io)

    if not text:
        await message.answer('Не удалось распознать текст')
    else:
        data_voice = await work_with_voice_text(session, user_id, text)

        text = await voice_result(session, data_voice,user_id)

        await message.answer(text)


class Money(StatesGroup):
    income_or_expense = State()
    category_name = State()
    category_id = State()
    delete_category_name = State()
    delete_category_id = State()
    add_category_name = State()
    wallet = State()
    wallet_id = State()
    suma = State()

# добавить категорию
@user_private_router.message(Money.category_name, F.text.lower().contains("добавить категорию"))
async def add_category_1(message: types.Message, state: FSMContext, session: AsyncSession) -> Message | None:
    text = f'Напишите название категории или нескольких категорий'

    await message.answer(text, reply_markup=reply.start_back.as_markup(resize_keyboard=True))

    await state.set_state(Money.add_category_name)

@user_private_router.message(Money.add_category_name, F.text)
async def add_category_1(message: types.Message, state: FSMContext, session: AsyncSession) -> Message | None:
    print(message.text)
    print(message.text.split(','))

    data = await state.get_data()
    cat_type = await orm_get_category_types_id(session, data["income_or_expense"])

    for cat in message.text.split(','):
        print(cat)
        data = {
            "user_id": message.from_user.id,
            "category_name": cat,
            "category_type_id": cat_type
        }
        await orm_add_category(session, data)

    await message.answer('Категории успешно добавлены')

@user_private_router.message(Money.category_name, F.text.lower().contains("удалить категорию"))
async def add_category_1(message: types.Message, state: FSMContext, session: AsyncSession) -> Message | None:
    text = f'Выберите категории,которые хотите удалить'

    data = await state.get_data()
    await message.answer('fff', reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    data = {"user_id": message.from_user.id, "category_type_name": data['income_or_expense']}

    cats = await orm_get_user_category(session, data)

    inline_kb_cat = dynamics_inline_kb_money(cats,btn_complite=True)
    await message.answer(text, reply_markup=inline_kb_cat.as_markup(resize_keyboard=True))

    await state.set_state(Money.delete_category_name)

@user_private_router.callback_query(Money.delete_category_name, F.data)
async def add_category_1(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> Message | None:
    try:
        cat_name, cat_id = ast.literal_eval(callback.data)
    except ValueError:
        cat_name = callback.data

    data = await state.get_data()
    await callback.message.delete()

    if cat_name == 'Готово':

        print(data)

        for cat_id in data['delete_category_id']:
            await orm_delete_category(session,cat_id, callback.from_user.id)

        d = {'user_id': callback.from_user.id, 'category_type_name': data['income_or_expense']}
        print(d)
        check = await orm_get_user_category(session,d)

        print('check: ',check)

        if not check:
            print('Мой тип:', data['income_or_expense'])
            storage_type_id = await orm_get_category_types_id(session, data['income_or_expense'])
            print('id:', storage_type_id)
            await orm_add_category(session, {'category_name': 'Прочее',
                                             'user_id': callback.from_user.id,
                                             'category_type_id': storage_type_id})
            print(111111)


        await callback.message.answer('Категории успешно удалены')

        preview = Bold("Выберите категорию:")
        data = {"user_id": callback.from_user.id, "category_type_name": data['income_or_expense']}

        cats = await orm_get_user_category(session, data)

        inline_kb_cat = dynamics_inline_kb_money(cats)
        await callback.message.answer(preview.as_html(), reply_markup=inline_kb_cat.as_markup(resize_keyboard=True))
        await state.set_state(Money.category_name)

        return


    if data.get('delete_category_name') is None:
        del_cat_name = []
        del_cat_id = []
    else:
        del_cat_name = data['delete_category_name']
        del_cat_id = data['delete_category_id']

    if cat_name not in del_cat_name:
        del_cat_name.append(cat_name)
    else:
        del_cat_name.remove(cat_name)

    if cat_id not in del_cat_id:
        del_cat_id.append(cat_id)
    else:
        del_cat_id.remove(cat_id)

    await state.update_data(delete_category_name=del_cat_name)
    await state.update_data(delete_category_id=del_cat_id)

    text = f'Вы выбрали: {', '.join(del_cat_name)}'


    data = {"user_id": callback.from_user.id, "category_type_name": data['income_or_expense']}

    cats = await orm_get_user_category(session, data)

    inline_kb_cat = dynamics_inline_kb_money(cats,btn_complite=True)
    await callback.message.answer(text, reply_markup=inline_kb_cat.as_markup(resize_keyboard=True))

    await state.set_state(Money.delete_category_name)


@user_private_router.message(F.text == '➕ Добавить доходы/ ➖ расходы')
async def get_in_or_ex(message: types.Message, state: FSMContext):
    preview = Bold('Выберите интересующий вас пункт:')
    await message.answer(preview.as_html(),
                         reply_markup=reply.in_ex.as_markup(resize_keyboard=True))
    await state.set_state(Money.income_or_expense)


@user_private_router.message(Money.income_or_expense, F.text)
async def get_cat(message: types.Message, state: FSMContext, session: AsyncSession):
    in_or_ex = "Доход" if message.text == 'Доходы' else "Расход"
    await state.update_data(income_or_expense=in_or_ex)

    await message.answer('ff', reply_markup=reply.add_cat_kb.as_markup(resize_keyboard=True))
    preview = Bold("Выберите категорию:")

    data = {"user_id": message.from_user.id, "category_type_name": in_or_ex}

    cats = await orm_get_user_category(session, data)

    inline_kb_cat = dynamics_inline_kb_money(cats)
    await message.answer(preview.as_html(), reply_markup=inline_kb_cat.as_markup(resize_keyboard=True))
    await state.set_state(Money.category_name)

@user_private_router.callback_query(Money.category_name, F.data)
async def get_wallet(callback: types.CallbackQuery,state: FSMContext, session: AsyncSession):
    cat_name, cat_id = ast.literal_eval(callback.data)
    await state.update_data(category_name=cat_name)
    await state.update_data(category_id=cat_id)
    await callback.message.delete()
    preview = (
                f'<b>Выбранная категория</b>: {cat_name}\n\n'
                f'<b>Выберите кошелёк:</b>'
    )

    data = {'user_id': callback.from_user.id, 'wallet_type_name': 'Кошелёк'}

    wallets = await orm_get_user_wallets(session, data)
    inline_kb_wal = dynamics_inline_kb_wallet(wallets)
    await callback.message.answer(preview, reply_markup=inline_kb_wal.as_markup(resize_keyboard=True))
    await state.set_state(Money.wallet)


@user_private_router.callback_query(Money.wallet, F.data)
async def get_suma(callback: types.CallbackQuery,state: FSMContext, session: AsyncSession):
    await state.update_data(wallet=callback.data)
    wallets = await orm_get_user_wallets_all(session, callback.from_user.id)
    for i in wallets:
        if i.wallet_name == callback.data:
            await state.update_data(wallet_id=i.wallet_id)
    data = await state.get_data()

    await callback.message.delete()
    preview = (
        f'<b>Выбранная категория</b>: {data['category_name']}\n\n'
        f'<b>Выбранный кошелёк:</b> {data['wallet']}\n\n'
        f'<b>Напишите сумму (число):</b>'
    )
    await callback.message.answer(preview, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await state.set_state(Money.suma)


@user_private_router.message(Money.suma, F.text)
async def add_income(message: Message, state: FSMContext, session: AsyncSession):
    try:
        suma = float(message.text)
    except ValueError:
        await message.answer('❌ Ошибка: Вы ввели не числовое значение\n\nВведите сумму заново')
        return


    if suma > 1_000_000:
        await message.answer_photo(photo=types.FSInputFile(path='./joke.jpg'))
    # if not message.text.isdigit():
    #     text = "Ошибка: введите число. Допустимы только цифры без лишних символов."
    #     await message.answer(text, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    #     await state.set_state(Money.suma)
    elif suma <= 0:
        await message.answer('❌ Ошибка: Число должно быть положительным\n\nВведите сумму заново')
        # text = "<b>Ошибка</b>: сумма должна быть больше нуля. Пожалуйста, введите корректное значение."
        # await message.answer(text, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
        # await state.set_state(Money.suma)
        return
    else:
        await state.update_data(suma=float(message.text))
        data = await state.get_data()
        data.update({'id': message.from_user.id})

        data_wal = {"wallet_id": data["wallet_id"], "suma": data["suma"], "cat_type": data["income_or_expense"],
                    'category_id': data['category_id']}

        await orm_add_category_transaction(session, data_wal)
        await orm_update_wallet_balance(session,data_wal)

        preview = Bold("Успешно добавлены")

        await message.answer(preview.as_html(), reply_markup=reply.start_back.as_markup(resize_keyboard=True))
