import datetime

import matplotlib.pyplot as plt
import io

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_category_transaction
from function.date import week, month, year


async def get_names_values(session: AsyncSession, all_cats: list, user_id: int, *time_period) -> (list, list):
    period = time_period[0]
    match period:
        case 'неделя':
            time_period = week('pie')
        case 'месяц':
            time_period = month('pie')
        case 'год':
            time_period = year('pie')

        case 'за всё время':
            time_period = False

        case _:
            time_period = time_period[0][0], time_period[0][1] + datetime.timedelta(days=1)

    print('time', time_period)
    if time_period:
        sum_cat = await orm_get_category_transaction(session, user_id, 'Расход', time_period)
    else:
        sum_cat = await orm_get_category_transaction(session, user_id, 'Расход')

    for i in sum_cat:
        print(i[0].transaction_date,i[0].amount, i[1] )

    sum_cat = sorted(sum_cat, key=lambda x: [cat.category_name for cat in all_cats].index(x[1]))


    res, i = {}, 0

    for cat in all_cats:

        for idx, sc in enumerate(sum_cat[i:]):
            if cat.category_name == sc[1]:
                if cat.category_name not in res:
                    res.update({cat.category_name: sc[0].amount})

                else:
                    res[cat.category_name] += sc[0].amount
            else:
                i += idx
                break

    names, values = [], []

    for name, val in res.items():
        names.append(name)
        values.append(float(val))

    print(names,values)
    return names, values


async def get_names_values_bar(session: AsyncSession, user_id: int, *time_period):
    period_choice = time_period[0]
    match period_choice:
        case 'неделя':
            time_period = week('bar')
            names = [f'{day[0].day if len(str(day[0].day)) == 2 else '0'+str(day[0].day)}.{day[0].month if len(str(day[0].month)) == 2 else '0'+str(day[0].month)}.{day[0].year}' for day in time_period]
            print(names)
            print(33333333, time_period)
        case 'месяц':
            time_period = month('bar')
            names = [f'{day[0].day if len(str(day[0].day)) == 2 else '0'+str(day[0].day)}.{day[0].month if len(str(day[0].month)) == 2 else '0'+str(day[0].month)}.{day[0].year}-{(day[1] - datetime.timedelta(days=1)).strftime("%d.%m.%Y")}' for day in
                     time_period]
        case 'год':
            time_period = year('bar')
            names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                     'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][:len(time_period)]

        case 'за всё время':
            time_period = False
            names = ['За всё время']

        case _:
            names = [f'{time_period[0][0].strftime("%d.%m.%Y")}-{time_period[0][1].strftime("%d.%m.%Y")}']
            time_period = ((time_period[0][0], time_period[0][1] + datetime.timedelta(days=1)),)

    print(1, names)

    if time_period:
        print(2222222222, time_period)
        expe = [await orm_get_category_transaction(session, user_id,'Расход', period) for period in time_period]
        inco = [await orm_get_category_transaction(session, user_id,'Доход', period) for period in time_period]

        expenses, incomes = [], []

        match period_choice:
            case 'неделя':
                names = names[::-1]
                for name in names:
                    expenses.extend([sum([float(k[0].amount) if name == k[0].transaction_date.strftime("%d.%m.%Y") else 0 for k in expe[0]])])
                    incomes.extend([sum([float(k[0].amount)  if name == k[0].transaction_date.strftime("%d.%m.%Y") else 0 for k in inco[0]])])

            case 'месяц':
                for name in names:
                    name = name.split('-')
                    expenses.extend([sum(
                        [float(k[0].amount) if name[0] <= k[0].transaction_date.strftime("%d.%m.%Y") <= name[1] else 0 for k in
                         expe[0]])])
                    incomes.extend([sum(
                        [float(k[0].amount) if name[0] <= k[0].transaction_date.strftime("%d.%m.%Y") <= name[1] else 0 for k in
                         inco[0]])])

            case 'год':
                for idx, name in enumerate(names):
                    print(idx+1)
                    expenses.extend([sum(
                        [float(k[0].amount) if idx+1 == int(k[0].transaction_date.month) else 0 for k in
                         expe[0]])])
                    incomes.extend([sum(
                        [float(k[0].amount) if idx+1 == int(k[0].transaction_date.month) else 0 for k in
                         inco[0]])])
        # select(CategoryTransaction, Category.category_name, Wallet.wallet_name)
        # select(Expense.suma, Category.name, Expense.date)

        print(names, incomes, expenses)

    else:
        expe = await orm_get_category_transaction(session, user_id,'Расход')
        inco = await orm_get_category_transaction(session, user_id, 'Доход')

        expenses = [sum([float(i[0].amount) for i in expe])]
        incomes = [sum([float(i[0].amount) for i in inco])]
    return names, incomes, expenses


def expense_pie_chart(values: list, categories: list, text: str):
    plt.figure(figsize=(8, 8))

    def autopct_func(pct):
        if pct > 0.1:
            return '%1.1f%%' % pct
        else:
            return '%1.2f%%' % pct

    # Вносим логику динамического отображения
    wedges, texts, autotexts = plt.pie(values, labels=categories, autopct=autopct_func,
                                       textprops={'fontsize': 10},
                                       pctdistance=0.7, labeldistance=1.05,
                                       wedgeprops={'edgecolor': 'white', 'linewidth': 0.4})

    print(values)

    # Функция для поворота меток
    def rotatelabels_func(texts, values):
        for idx, text in enumerate(texts):
            x, y = text.get_position()
            if abs(x) > 0.6 and abs(y) < 0.75:

                if values[idx] / sum(values) < 0.01:
                    x = x
                    if y > 0:
                        y = y + y * 1.7
                    else:
                        y = y - abs(y) * 1.7
                    text.set_position((x, y))

    # Применение функции для ротации меток
    rotatelabels_func(texts, values)

    # Сдвигаем только проценты для маленьких долей
    for i, autotext in enumerate(autotexts):
        if values[i] / sum(values) < 0.05:
            autotext.set_position(
                (1.23 * autotext.get_position()[0], 1.23 * autotext.get_position()[1]))  # сдвигаем процент наружу

    plt.title(f'Распределение расходов {text}', fontsize=15, fontweight='bold')
    plt.tight_layout()
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()

    # Возвращаем изображение из памяти
    img_bytes.seek(0)  # перемещаем указатель в начало
    return img_bytes


def in_ex_bar_chart(months: list, income: list, expenses: list):
    if len(months) < 2:
        size_in_bar = 25
        size_on_bar = 25
    else:
        size_in_bar = 8
        size_on_bar = 10

    bar_width = 2.5  # Увеличиваем ширину столбцов
    gap = 6.2
    # Позиции столбцов
    r1 = np.arange(len(months)) * gap
    r2 = [x + bar_width for x in r1]

    # Рассчитываем разницу между доходами и расходами
    difference_ex = [i - e if i - e > 0 else 0 for i, e in zip(income, expenses)]
    print(difference_ex)
    difference_in = [e - i if e - i > 0 else 0 for i, e in zip(income, expenses)]
    print(difference_in)
    # Определение максимального значения доходов и расходов
    max_value = max(max(income), max(expenses))

    # Создание графика
    plt.figure(figsize=(12, 12))

    # Построение вертикальных столбчатых графиков доходов и расходов
    bars1 = plt.bar(r1, income, color='#4CAF50', width=bar_width, edgecolor='grey', label='Доходы')
    bars2 = plt.bar(r2, expenses, color='#616161', width=bar_width, edgecolor='grey', label='Расходы')
    bars3 = plt.bar(r2, difference_ex, bottom=expenses, color='#616161', alpha=0.3, width=bar_width, edgecolor='grey')
    bars4 = plt.bar(r1, difference_in, bottom=income, color='#4CAF50', alpha=0.3, width=bar_width, edgecolor='grey')

    # Добавление заголовка и меток осей
    plt.title('Доходы и расходы по месяцам', fontsize=15)
    plt.ylabel('Сумма (руб.)', fontsize=15)
    plt.xlabel('Месяцы', fontsize=15)

    # Добавление меток на ось X
    plt.xticks([r + bar_width / 2 for r in r1], months)

    # Добавление легенды
    plt.legend()
    # Добавление числовых меток с настройками для улучшения видимости
    for i in [zip(bars1, difference_in), zip(bars2, difference_ex)]:
        for bar, diff in i:
            xval = bar.get_x() + bar.get_width() / 2
            # Изменяем шрифт на меньший и центрируем текст внутри столбца
            plt.text(xval, bar.get_height() / 2, f'{bar.get_height():.0f}', va='center', ha='center', color='white',
                     fontsize=size_in_bar)
            if diff > 0:
                plt.text(xval, bar.get_height() + diff, f'{diff / (bar.get_height() + diff) * 100:.1f}%', va='bottom',
                         ha='center', color='black', fontsize=size_on_bar)

    # Установка пределов по оси Y
    plt.ylim(0, max_value * 1.1)

    # Показ графика
    # plt.grid(True)
    plt.tight_layout()  # Автоматическая настройка макета для избежания перекрытия меток

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()

    # Возвращаем изображение из памяти
    img_bytes.seek(0)  # перемещаем указатель в начало
    return img_bytes
