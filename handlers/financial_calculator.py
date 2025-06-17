import datetime
from dateutil.relativedelta import relativedelta
from aiogram import types, Router, F, Bot
import re
from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile, BufferedInputFile
from aiogram.utils.formatting import as_list, as_marked_section, Bold, Italic, Text

from function.money_conversion import conversion
from keyboards import reply, inline_kb

import io

finance_router = Router()


@finance_router.message(F.text == 'Финансовый калькулятор 🧮')
async def fin_cal(message: types.Message):
    preview = Bold('Выберите интересующий вас пункт')
    await message.answer(preview.as_html(), reply_markup=reply.fin_cal.as_markup(resize_keyboard=True))


class ConvertеrMoney(StatesGroup):
    suma = State()
    id_val = State()
    id_val_wish = State()

    texts = {
        'ConvertеrMoney:suma': 'Напишите сумму заново',
        'ConvertеrMoney:id_val': 'Выберите валюту заново',
        'ConvertеrMoney:id_val_wish': 'Выберите заново валюту в которую хотите перевести',
    }


#Вернутся на шаг назад (на прошлое состояние)
@finance_router.message(StateFilter('*'), F.text.lower().contains("вернуться назад"))
async def back_step_handler(message: types.Message, state: FSMContext) -> Message | None:
    current_state = await state.get_state()

    previous = None

    if current_state in ConvertеrMoney.__all_states__:
        for step in ConvertеrMoney.__all_states__:
            if step.state == current_state:
                info = f"Вы вернулись к прошлому шагу \n\n<b>{ConvertеrMoney.texts[previous.state]}</b>"
                await state.set_state(previous)

                match previous.state:
                    case ConvertеrMoney.suma:
                        await message.answer(f'{info}', reply_markup=reply.start_back.as_markup(resize_keyboard=True))

                    case ConvertеrMoney.id_val:
                        await message.answer(f'{info}', reply_markup=inline_kb.inline_money.as_markup())

                    case ConvertеrMoney.id_val_wish:
                        await message.answer(f'{info}', reply_markup=inline_kb.inline_money.as_markup())

                return
            previous = step


@finance_router.message(F.text == 'Конвектор валют')
async def converter_1(message: types.Message, state: FSMContext):
    preview = Bold('Напишите интересующую вас сумму:')

    await message.answer(preview.as_html(), reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await state.set_state(ConvertеrMoney.suma)


@finance_router.message(ConvertеrMoney.suma, F.text)
async def converter_2(message: types.Message, state: FSMContext):
    await state.update_data(suma=float(message.text))

    preview = Bold(f'Первоначальная валюта ➡️')

    await message.answer(preview.as_html(), reply_markup=inline_kb.inline_money.as_markup())
    await state.set_state(ConvertеrMoney.id_val)


@finance_router.callback_query(StateFilter('*'), lambda c: c.data in ['byn', 'usd', 'eur', 'rub', 'cny', 'pln'])
async def converter_3(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    selected_currency = callback.data

    match current_state:

        case ConvertеrMoney.id_val:
            await state.update_data(id_val=selected_currency)

            preview = Bold(f'Первоначальная валюта ➡️ {selected_currency}\nПеревод в ➡️')
            await callback.message.edit_text(preview.as_html(), reply_markup=inline_kb.inline_money.as_markup())
            await state.set_state(ConvertеrMoney.id_val_wish)

        case _:
            await state.update_data(id_val_wish=selected_currency)
            await callback.message.delete()
            data = await state.get_data()
            await callback.message.answer(
                f'Первоначальная валюта ➡️ {data['id_val']}\nПеревод в ➡️ {selected_currency}')

            res = conversion(data['suma'], data['id_val'], data['id_val_wish'])

            preview = f'Ваша сумма - <b>{data['suma']} {data['id_val']}</b>\nЭто - <b>{res} {data['id_val_wish']}</b>'
            await callback.message.answer(preview)


class Deposit(StatesGroup):
    suma = State()
    period = State()
    term = State()
    start_date = State()
    proc = State()
    par = State()
    res = State()
    n = State()
    k = State()


@finance_router.message(F.text == 'Расчёт вклада')
async def deposit_1(message: types.Message, state: FSMContext):
    preview = f'💰 Введите сумму вклада (например: 1000)'

    await message.answer(preview, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await state.set_state(Deposit.suma)


@finance_router.message(Deposit.suma, F.text)
async def deposit_2(message: Message, state: FSMContext):
    try:
        suma = float(message.text)
    except ValueError:
        await message.answer('❌ Ошибка: Вы ввели не числовое значение\n\nВведите сумму вклада заново')
        return

    if suma <= 0:
        await message.answer('❌ Ошибка: Число должно быть положительным\n\nВведите сумму вклада заново')
        return

    await state.update_data(suma=suma)
    preview = (f'Сумма вклада: <b>{suma}</b>\n\n'
               f'📅 Выберите единицу измерения срока:\n'
               f'▫️ Дни\n'
               f'▫️ Месяцы\n'
               f'▫️ Годы\n'
               )
    await message.answer(preview,
                         reply_markup=reply.period_kb_deposit.as_markup(resize_keyboard=True))
    await state.set_state(Deposit.period)


@finance_router.message(Deposit.period, F.text)
async def deposit_2(message: Message, state: FSMContext):
    if message.text not in ["Дни", "Месяцы", "Годы"]:
        await message.answer(
            '❌ Ошибка: Неверная единица измерения срока\n\nВыберите подходящую единицу измерения заново')
        return

    await state.update_data(period=message.text)

    match message.text.lower():
        case "дни":
            period = "днях"
        case "месяцы":
            period = "месяцах"
        case "годы":
            period = "годах"

    await state.update_data(period=message.text)
    data = await state.get_data()
    preview = (
        f'Сумма вклада: <b>{data["suma"]}</b>\n'
        f'Единица измерения срока: <b>{data["period"]}</b>\n\n'
        f'⏱ Введите срок вклада в <b>{period}</b> (например: 13)')
    await message.answer(preview,
                         reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await state.set_state(Deposit.term)


@finance_router.message(Deposit.term, F.text)
async def deposit_3(message: Message, state: FSMContext):
    try:
        term = int(message.text)
    except ValueError:
        if '.' in message.text and message.text.replace(".",'').isdigit():
            await message.answer('❌ Ошибка: Вы ввели не целочисленное значение\n\nВведите срок вклада заново')
            return
        await message.answer('❌ Ошибка: Вы ввели не числовое значение\n\nВведите срок вклада заново')
        return

    if term <= 0:
        await message.answer('❌ Ошибка: Срок вклада должен быть положительным\n\nВведите срок вклада заново')
        return

    await state.update_data(term=term)
    data = await state.get_data()

    preview = (
        f'Сумма вклада: <b>{data["suma"]}</b>\n'
        f'Единица измерения срока: <b>{data["period"]}</b>\n'
        f'Срок вклада : <b>{data["term"]}</b>\n\n'
        f'🗓 Введите дату начала вклада в формате ГГГГ.ММ.ДД (например: 2025.01.01)'
    )
    await message.answer(preview,
                         reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await state.set_state(Deposit.start_date)


@finance_router.message(Deposit.start_date, F.text)
async def deposit_3(message: Message, state: FSMContext):
    flag = re.search(r'\d{4}.[0-1]{1}[1-9]{1}.[0-3]{1}[0-9]{1}', message.text)
    if flag:
        b = list(map(int, message.text.split('.')))
        try:
            date = datetime.datetime(b[0], b[1], b[2])
        except ValueError:
            await message.answer(
                '❌ Ошибка: Дата не существует\n\nВведите дату начала вклада заново')
            return
    else:
        await message.answer('❌ Ошибка: Неправильный формат даты начала вклада\n\nВведите дату начала вклада заново')
        return

    await state.update_data(start_date=date)
    data = await state.get_data()

    preview = (
        f'Сумма вклада: <b>{data["suma"]}</b>\n'
        f'Единица измерения срока: <b>{data["period"]}</b>\n'
        f'Срок вклада : <b>{data["term"]}</b>\n'
        f'Дата открытия вклада: <b>{data["start_date"].strftime("%Y.%m.%d")}</b>\n\n'
        f'📈 Введите процентную ставку (например: 13)'
    )

    await message.answer(preview,
                         reply_markup=reply.start_back.as_markup(resize_keyboard=True))
    await state.set_state(Deposit.proc)


@finance_router.message(Deposit.proc, F.text)
async def deposit_4(message: Message, state: FSMContext):
    try:
        proc = float(message.text)
    except ValueError:
        await message.answer('❌ Ошибка: Вы ввели не числовое значение\n\nВведите процентную ставку заново')
        return

    if proc <= 0:
        await message.answer(
            '❌ Ошибка: Процентная ставка должна быть положительная\n\nВВведите процентную ставку заново')
        return

    await state.update_data(proc=proc)
    data = await state.get_data()

    preview = (
        f'Сумма вклада: <b>{data["suma"]}</b>\n'
        f'Единица измерения срока: <b>{data["period"]}</b>\n'
        f'Срок вклада : <b>{data["term"]}</b>\n'
        f'Дата открытия вклада: <b>{data["start_date"].strftime("%Y.%m.%d")}</b>\n'
        f'Процентная ставка: <b>{data["proc"]}</b>\n\n'
        f'⚙️ Выберите дополнительные параметры вклада или перейдите к расчёту, нажав «Готово»'
    )

    await message.answer(preview,
                         reply_markup=reply.vklad_par.as_markup(resize_keyboard=True))
    await state.set_state(Deposit.par)


@finance_router.message(Deposit.par, F.text)
async def deposit_4(message: Message, state: FSMContext):
    data = await state.get_data()

    par_lst = data["par"] if data.get("par") else {}

    if par_lst.get("Пополнение"):
        if par_lst.get("Пополнение")[1] == -1 and par_lst.get("Пополнение")[0] != -1:
            par_lst["Пополнение"] = [par_lst.get("Пополнение")[0], float(message.text)]

    match message.text:
        case "Готово":
            await state.set_state(Deposit.res)
            await deposit_5(message, state)
            return
        case "Капитализация":
            if "Капитализация" in par_lst:
                par_lst.pop("Капитализация")
            else:
                await message.answer("Выберите периодичность капитализации",
                                     reply_markup=reply.period_capital.as_markup(resize_keyboard=True))
                par_lst["Капитализация"] = -1
        case "Пополнение":
            if "Пополнение" in par_lst:
                par_lst.pop("Пополнение")
            else:
                await message.answer("Выберите периодичность пополнения",
                                     reply_markup=reply.period_capital.as_markup(resize_keyboard=True))
                par_lst["Пополнение"] = [-1, -1]
        case _:
            pass

    await state.update_data(par=par_lst)

    if par_lst.get("Капитализация") and par_lst.get("Капитализация") == -1:
        if message.text == "Капитализация":
            return
        match message.text:
            case "Ежемесячно":
                par_lst["Капитализация"] = "Ежемесячно"
            case "Ежегодно":
                par_lst["Капитализация"] = "Ежегодно"

    elif par_lst.get("Пополнение") and par_lst.get("Пополнение")[0] == -1:
        if message.text == "Пополнение":
            return
        match message.text:
            case "Ежемесячно":
                par_lst["Пополнение"] = ["Ежемесячно", -1]
            case "Ежегодно":
                par_lst["Пополнение"] = ["Ежегодно", -1]

        await state.update_data(par=par_lst)

        await message.answer("Напишите сумму на которую собираетесь пополнять")
        return

    if par_lst:
        summary = '\n'.join(
            f"- {key} ({', '.join(map(str, value)) if isinstance(value, list) else value})" for key, value in
            par_lst.items())
        strform = (
            f'Сейчас выбрано:\n<b>{summary}</b>\n\n'
            f'⚙️ Выберите дополнительный параметр вклада или перейдите к расчёту, нажав «Готово»'
        )
    else:
        strform = (
            f'⚙️ Выберите дополнительные параметры вклада или перейдите к расчёту, нажав «Готово»'
        )

    preview = (
        f'Сумма вклада: <b>{data["suma"]}</b>\n'
        f'Единица измерения срока: <b>{data["period"]}</b>\n'
        f'Срок вклада : <b>{data["term"]}</b>\n'
        f'Дата открытия вклада: <b>{data["start_date"].strftime("%Y.%m.%d")}</b>\n'
        f'Процентная ставка: <b>{data["proc"]}</b>\n\n'
        f'{strform}'
    )

    await state.update_data(par=par_lst)
    await message.answer(preview,
                         reply_markup=reply.vklad_par.as_markup(resize_keyboard=True))


@finance_router.message(Deposit.res)
async def deposit_5(message: Message, state: FSMContext):
    data = await state.get_data()
    match data["period"].lower():
        case "дни":
            term = data["term"] / 365
            time_delta = datetime.timedelta(days=data["term"])
        case "месяцы":
            term = data["term"] / 12
            if data["term"] > 12:
                year = data["term"] // 12
                month = data["term"] - year * 12
                time_delta = relativedelta(years=year, months=month)
            else:
                time_delta = relativedelta(months=data["term"])
        case "годы":
            term = data["term"]
            time_delta = relativedelta(year=data["term"])

    if not data.get("par"):
        result = data['suma'] * (1 + (data['proc'] * term) / 100)

    else:
        if data["par"].get("Капитализация"):
            n = 12 if data["par"].get("Капитализация") == "Ежемесячно" else 1
        if data["par"].get("Пополнение"):
            k = 12 if data["par"].get("Пополнение")[0] == "Ежемесячно" else 1
            add_sum = data["par"].get("Пополнение")[1]
            dop_sum = add_sum * 12 * term
        if len(data["par"]) == 1:
            if "Капитализация" in data["par"]:
                result = data['suma'] * (1 + data['proc'] / (100 * n)) ** (n * term)
            elif "Пополнение" in data["par"]:
                result = (data['suma'] + add_sum * k * term + (data['suma'] + add_sum * (k * term + 1) / 2) * term * (
                            data['proc'] / 100))
            else:
                result = 0
        else:
            result = data['suma'] * (1 + data['proc'] / (100 * n)) ** (n * term) + add_sum * (
                        ((1 + data['proc'] / (100 * n)) ** (n * term) - 1) / (
                            (1 + data['proc'] / (100 * n)) ** (n / k) - 1))

    if data["par"].get("Пополнение"):
        ans = round(round(result, 2) - data["suma"] - dop_sum, 2)
    else:
        ans = round(round(result, 2) - data["suma"], 2)



    last_date = data["start_date"] + time_delta
    preview = (
        f'Продолжительность вклада: <b>{data["start_date"].strftime("%Y.%m.%d")} - {last_date.strftime("%Y.%m.%d")}</b>\n\n'
        f'Итоговая сумма к выдаче: <b>{round(result, 2)}</b>\n'
        f"Полученный доход: <b>{ans}</b>"

    )

    await message.answer(preview, reply_markup=reply.start_back.as_markup(resize_keyboard=True))
