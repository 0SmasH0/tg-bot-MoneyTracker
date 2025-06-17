import datetime
import re

from aiogram import types, Router, F, Bot

from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, FSInputFile, InputFile, BufferedInputFile
from aiogram.utils.formatting import as_list, as_marked_section, Bold, Italic, Text
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_user_category
# from database.orm_query import get_user_categories, orm_get_expenses
from function.date import week, month, year

from function.diagrams import get_names_values, expense_pie_chart, get_names_values_bar, in_ex_bar_chart

# from function.diagrams import expense_pie_chart, in_ex_bar_chart, get_names_values, get_names_values_bar
from keyboards import reply, inline_kb

reports_router = Router()


class ViewReports(StatesGroup):
    view = State()
    time_period = State()
    custom_time = State()


@reports_router.message(F.text == 'Отчёты 📊')
async def reports(message: types.Message, state: FSMContext):
    preview = Bold('Выберите интересующий вас вид отчёта:')
    await message.answer(preview.as_html(),
                         reply_markup=reply.diagram_report.as_markup(resize_keyboard=True))

    await state.set_state(ViewReports.view)


@reports_router.message(ViewReports.view, lambda c: c.text in ['Круговая диаграмма расходов', 'Столбчатая диаграмма'])
async def reports_2(message: types.Message, state: FSMContext):
    await state.update_data(view=message.text)
    preview = Bold('Выберите интересующий вас период времени:')
    await message.answer(preview.as_html(),
                         reply_markup=reply.time_period.as_markup(resize_keyboard=True))

    await state.set_state(ViewReports.time_period)


@reports_router.message(ViewReports.time_period, F.text)
async def reports_3(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(time_period=message.text.lower())
    data = await state.get_data()

    if data['time_period'] == 'написать свой период времени':
        await message.answer(f'Напишите нужный вам период\n\nСледующий шаблон:\n<b>день.месяц.год-день.месяц.год</b>')
        await state.set_state(ViewReports.custom_time)

    else:
        if data['view'] == 'Круговая диаграмма расходов':

            all_cats = await orm_get_user_category(session, {'user_id': message.from_user.id, 'category_type_name': "Расход"})
            names, values = await get_names_values(session, all_cats, message.from_user.id, data['time_period'])

            chart_bytes = expense_pie_chart(values, names, message.text.lower())
            chart_file = BufferedInputFile(chart_bytes.read(), filename='expense_pie_chart.png')

            await message.answer_photo(chart_file, caption="Круговая диаграмма расходов",
                                       reply_markup=reply.diagram_report.as_markup(resize_keyboard=True))

        elif data['view'] == 'Столбчатая диаграмма':
            names, income, expenses = await get_names_values_bar(session, message.from_user.id, data['time_period'])
            chart_bytes = in_ex_bar_chart(names, income, expenses)
            chart_file = BufferedInputFile(chart_bytes.read(), filename='in_ex_bar_chart.png')

            await message.answer_photo(chart_file, caption="Столбчатая диаграмма",
                                       reply_markup=reply.diagram_report.as_markup(resize_keyboard=True))



@reports_router.message(ViewReports.custom_time, F.text)
async def reports_4(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(custom_time=message.text.lower())
    data = await state.get_data()

    time_period = re.findall(r'\d{1,2}\.\d{1,2}\.\d{4}', data['custom_time'])

    if len(time_period) == 1:
        await message.answer('Вы указали время неправильно')

    else:
        date_object = datetime.datetime.strptime(time_period[0], "%d.%m.%Y").date()
        date_object_2 = datetime.datetime.strptime(time_period[1], "%d.%m.%Y").date()
        if date_object > date_object_2:
            date_object, date_object_2 = date_object_2, date_object

        date = date_object, date_object_2

        if data['view'] == 'Круговая диаграмма расходов':
            all_cats = await orm_get_user_category(session, {'user_id': message.from_user.id, 'category_type_name': "Расход"})
            names, values = await get_names_values(session, all_cats, message.from_user.id, date)
            print(names, values)

            chart_bytes = expense_pie_chart(values, names, message.text.lower())
            chart_file = BufferedInputFile(chart_bytes.read(), filename='expense_pie_chart.png')

            await message.answer_photo(chart_file, caption="Круговая диаграмма расходов",
                                       reply_markup=reply.diagram_report.as_markup(resize_keyboard=True))

        if data['view'] == 'Столбчатая диаграмма':
            names, income, expenses = await get_names_values_bar(session, message.from_user.id, date)
            print(11111111, names,income,expenses)
            chart_bytes = in_ex_bar_chart(names, income, expenses)
            chart_file = BufferedInputFile(chart_bytes.read(), filename='in_ex_bar_chart.png')

            await message.answer_photo(chart_file, caption="Столбчатая диаграмма",
                                       reply_markup=reply.diagram_report.as_markup(resize_keyboard=True))
