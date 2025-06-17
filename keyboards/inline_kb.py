from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Конвертация валют
inline_money = InlineKeyboardBuilder()
inline_money.add(
    InlineKeyboardButton(text='USD 🇺🇸', callback_data='usd'),
    InlineKeyboardButton(text='EUR 🇪🇺', callback_data='eur'),
    InlineKeyboardButton(text='RUB 🇷🇺', callback_data='rub'),
    InlineKeyboardButton(text='CNY 🇨🇳', callback_data='cny'),
    InlineKeyboardButton(text='PLN 🇵🇱', callback_data='pln'),
    InlineKeyboardButton(text='BYN 🇧🇾', callback_data='byn')
)
inline_money.adjust(3, 3)


# Профиль пользователя
inline_profile = InlineKeyboardBuilder()
inline_profile.add(
    InlineKeyboardButton(text='История операций', callback_data='history'),
    InlineKeyboardButton(text='Сбросить данные аккаунта', callback_data='drop_data_user')
)
inline_profile.adjust(1)


# Правильные размеры клавиатуры
def create_kb(data: list):
    length = len(data) # 3
    count = length // 3 # 1
    fin_sizes = [3] * count + [length - 3 * count]
    return fin_sizes

def create_kb_with_special_btn(data: list):
    length = len(data) - 1 # 2
    count = length // 3 # 0
    fin_sizes = [3] * count + [length - 3 * count] + [1]
    return fin_sizes

def dynamics_inline_kb_options(options: list):
    inline_options = InlineKeyboardBuilder()
    inline_options.add(
        *[InlineKeyboardButton(text=f'{option}', callback_data=f'{option}') for option in options]
    )

    inline_options.adjust(*[1]*len(options))

    return inline_options

# Категории пользователя дохода или расхода
def dynamics_inline_kb_money(categories: list, btn_complite=False):
    sizes = create_kb(categories)
    inline_categories = InlineKeyboardBuilder()
    print(categories)
    inline_categories.add(
        *[InlineKeyboardButton(text=f'{cat.category_name}', callback_data=f'{cat.category_name,cat.category_id}') for cat in categories]
    )
    if btn_complite:
        categories.append('Готово')
        sizes = create_kb_with_special_btn(categories)
        inline_categories.add(
            InlineKeyboardButton(text=f'Готово', callback_data=f'Готово')
        )
        inline_categories.adjust(*sizes)
        return inline_categories
    inline_categories.adjust(*sizes)

    return inline_categories

def dynamics_inline_kb_wallet(wallets: list):
    sizes = create_kb(wallets)
    inline_categories = InlineKeyboardBuilder()
    inline_categories.add(
        *[InlineKeyboardButton(text=f'{wallet.wallet_name}', callback_data=f'{wallet.wallet_name}') for wallet in wallets]
    )

    inline_categories.adjust(*sizes)

    return inline_categories


def dynamics_inline_kb_wallet_name_id(wallets: list):
    sizes = create_kb(wallets)
    inline_storage = InlineKeyboardBuilder()
    inline_storage.add(
        *[InlineKeyboardButton(text=f'{wallet.wallet_name}', callback_data=f'{wallet.wallet_name, wallet.wallet_id}') for wallet in wallets]
    )

    inline_storage.adjust(*sizes)

    return inline_storage

def dynamics_inline_kb_budget_name_id(budgets: list):
    sizes = create_kb(budgets)
    inline_storage = InlineKeyboardBuilder()
    inline_storage.add(
        *[InlineKeyboardButton(text=f'{budget[0]}', callback_data=f'{budget[0], budget[1]}') for budget in budgets]
    )

    inline_storage.adjust(*sizes)

    return inline_storage


def dynamics_inline_kb_period_name_id(periods: list):
    sizes = create_kb(periods)
    inline_storage = InlineKeyboardBuilder()
    inline_storage.add(
        *[InlineKeyboardButton(text=f'{period[0].period_name}', callback_data=f'{period[0].period_name, period[0].period_id}') for period in periods]
    )

    inline_storage.adjust(*sizes)

    return inline_storage

def dynamics_inline_kb_wallet_name_id_suma(wallets: list):
    sizes = create_kb(wallets)
    inline_storage = InlineKeyboardBuilder()
    inline_storage.add(
        *[InlineKeyboardButton(text=f'{wallet.wallet_name} ({wallet.balance})', callback_data=f'{wallet.wallet_name, wallet.wallet_id, float(wallet.balance)}') for wallet in wallets]
    )

    inline_storage.adjust(*sizes)

    return inline_storage