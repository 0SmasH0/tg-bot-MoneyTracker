from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

back_to_start = ReplyKeyboardBuilder()
back_to_start.add(
    KeyboardButton(text='Вернуться в начало🏠'),
)
back_to_start.adjust(1)

back_btn = ReplyKeyboardBuilder()
back_btn.add(
    KeyboardButton(text='Вернуться назад⬅️'),
)
back_btn.adjust(1)

start_back = ReplyKeyboardBuilder()
start_back.attach(back_btn)
start_back.attach(back_to_start)
start_back.adjust(1, 1)

budget_main_btn = ReplyKeyboardBuilder()
budget_main_btn.add(
    KeyboardButton(text='Добавить бюджет')
)
budget_main_btn.attach(start_back)
budget_main_btn.adjust(1,2)


start_kb = ReplyKeyboardBuilder()
start_kb.add(
    # Транзакции
    KeyboardButton(text='➕ Добавить доходы/ ➖ расходы'),
    KeyboardButton(text='Переводы 🔁'),
    KeyboardButton(text='Регулярные платежи 📅'),
    # Аналитика
    KeyboardButton(text='Отчёты 📊'),
    KeyboardButton(text='Бюджет 🧾'),
    KeyboardButton(text='Финансовый калькулятор 🧮'),
    # Профиль
    KeyboardButton(text='Счета 💼'),
    KeyboardButton(text='Профиль 👤'),
)
start_kb.adjust(3,3,2)



add_cat_kb = ReplyKeyboardBuilder()
add_cat_kb.add(
    KeyboardButton(text='Добавить категорию'),
    KeyboardButton(text='Удалить категорию')
)
add_cat_kb.attach(start_back)
add_cat_kb.adjust(1,1, 2)



fin_cal = ReplyKeyboardBuilder()
fin_cal.add(
    KeyboardButton(text='Конвектор валют'),
    KeyboardButton(text='Расчёт вклада'),
    KeyboardButton(text='Расчёт кредита'),

)
fin_cal.attach(back_to_start)
fin_cal.adjust(1, 1, 1, 1)

diagram_report = ReplyKeyboardBuilder()
diagram_report.add(
    KeyboardButton(text='Круговая диаграмма расходов'),
    KeyboardButton(text='Столбчатая диаграмма'),
)
diagram_report.attach(back_to_start)
diagram_report.adjust(1,1,1)

period_kb_deposit = ReplyKeyboardBuilder()
period_kb_deposit.add(
    KeyboardButton(text='Дни'),
    KeyboardButton(text='Месяцы'),
    KeyboardButton(text='Годы')
)
period_kb_deposit.attach(start_back)
period_kb_deposit.adjust(3, 2)

time_period = ReplyKeyboardBuilder()
time_period.add(
    KeyboardButton(text='Неделя'),
    KeyboardButton(text='Месяц'),
    KeyboardButton(text='Год'),
    KeyboardButton(text='За всё время'),
    KeyboardButton(text='Написать свой период времени'),

)
time_period.attach(start_back)
time_period.adjust(2, 2, 1, 2)

profile_kb_administration = ReplyKeyboardBuilder()
profile_kb_administration.add(
    KeyboardButton(text='Кошельки'),
            KeyboardButton(text='Вклады'),
            KeyboardButton(text='Цели')
)
profile_kb_administration.attach(back_to_start)
profile_kb_administration.adjust(1,1,1, 2)

def profile_add_storage_func(storage_name: str):
    profile_add_storage = ReplyKeyboardBuilder()
    profile_add_storage.add(
        KeyboardButton(text=f'Создать {storage_name.lower()}')
    )
    profile_add_storage.attach(start_back)
    profile_add_storage.adjust(1, 2)

    return profile_add_storage

vklad_par = ReplyKeyboardBuilder()
vklad_par.add(
    KeyboardButton(text='Капитализация'),
    KeyboardButton(text='Пополнение'),
    KeyboardButton(text='Готово')
)
vklad_par.attach(start_back)
vklad_par.adjust(2,1,2)

in_ex = ReplyKeyboardBuilder()
in_ex.add(
    KeyboardButton(text='Доходы'),
    KeyboardButton(text='Расходы'),
)
in_ex.attach(back_to_start)
in_ex.adjust(1,1,1)


budget_kb_administration = ReplyKeyboardBuilder()
budget_kb_administration.add(
    KeyboardButton(text='День'),
            KeyboardButton(text='Месяц'),
            KeyboardButton(text='Год')
)
budget_kb_administration.attach(back_to_start)
budget_kb_administration.adjust(1,1,1, 2)

period_capital = ReplyKeyboardBuilder()
period_capital.add(
    KeyboardButton(text='Ежемесячно'),
            KeyboardButton(text='Ежегодно'),
)
period_capital.attach(back_to_start)
period_capital.adjust(2,1)

