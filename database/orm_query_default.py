import datetime

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Currency, WalletType, CategoryType, Period


async def orm_add_currency(session: AsyncSession, data: dict):
    obj = Currency(currency_code=data["currency_code"], currency_fullname=data["currency_fullname"])

    session.add(obj)
    await session.commit()


async def orm_add_default_currency(session: AsyncSession):
    default_categories = {"EUR": "Евро", "USD": "Доллар США",
                          "BYN":"Белорусский рубль","RUB":"Российский рубль",
                          "PLN":"Польский злотый","CNY":"Китайский юань"}

    for key, value in default_categories.items():
        await orm_add_currency(session, {"currency_code":key, "currency_fullname":value})


async def orm_add_wallet_types(session: AsyncSession, data: str):
    obj = WalletType(wallet_type_name=data)

    session.add(obj)
    await session.commit()


async def orm_add_default_wallet_types(session: AsyncSession):
    default_wallet_types = ['Кошелёк', 'Вклад', 'Цель']

    for name in default_wallet_types:
        await orm_add_wallet_types(session, name)


async def orm_add_category_types(session: AsyncSession, data: str):
    obj = CategoryType(category_type_name=data)

    session.add(obj)
    await session.commit()

async def orm_add_period(session: AsyncSession, data: str):
    obj = Period(period_name=data)

    session.add(obj)
    await session.commit()


async def orm_add_default_category_types(session: AsyncSession):
    default_category_type = ['Доход', 'Расход']

    for name in default_category_type:
        await orm_add_category_types(session, name)


async def orm_add_default_periods(session: AsyncSession):
    default_periods = ['День', 'Месяц', 'Год']

    for name in default_periods:
        await orm_add_period(session, name)

