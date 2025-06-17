import datetime

from requests import session
from sqlalchemy import select, update, delete, func, and_, insert, exists, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased

from database.models import (User, Category, UserCategory, Wallet, RecurringPayment, Budget,
                             WalletType, WalletInvestment, WalletTarget, CategoryType, WalletTransfer,
                             CategoryTransaction,Currency,Period)


# Добавляем пользователя
async def orm_add_user(session: AsyncSession, data: dict):
    obj = User(user_id=data['user_id'], username=data['username'])

    session.add(obj)
    await session.flush()
    await session.commit()


async def orm_wipe_user_data(session: AsyncSession, user_id: int):
    # Получаем wallet_id'ы пользователя
    result = await session.execute(
        select(Wallet.wallet_id).where(Wallet.user_id == user_id)
    )
    wallet_ids = [row[0] for row in result.fetchall()]
    print(wallet_ids)

    # Удаляем регулярные платежи
    await session.execute(
        delete(RecurringPayment).where(RecurringPayment.wallet_id.in_(wallet_ids))
    )

    # Удаляем транзакции
    await session.execute(
        delete(WalletTransfer).where(WalletTransfer.source_wallet_id.in_(wallet_ids))
    )
    await session.execute(
        delete(WalletTransfer).where(WalletTransfer.target_wallet_id.in_(wallet_ids))
    )

    await session.execute(
        delete(CategoryTransaction).where(CategoryTransaction.wallet_id.in_(wallet_ids))
    )
    # Удаляем свойства кошельков
    await session.execute(
        delete(WalletInvestment).where(WalletInvestment.wallet_id.in_(wallet_ids))
    )
    await session.execute(
        delete(WalletTarget).where(WalletTarget.wallet_id.in_(wallet_ids))
    )

    # Удаляем кошельки
    await session.execute(
        delete(Wallet).where(Wallet.user_id == user_id)
    )

    # Удаляем бюджеты
    await session.execute(
        delete(Budget).where(Budget.user_id == user_id)
    )

    # 5. Удаляем связи с категориями
    user_categories_query = select(UserCategory).where(UserCategory.user_id == user_id)
    user_categories_result = await session.execute(user_categories_query)
    user_categories = user_categories_result.scalars().all()

    # Список категорий для удаления
    categories_to_delete = []

    for user_category in user_categories:
        # 6. Проверяем, есть ли такая категория у других пользователей
        other_users_query = (select(func.count(UserCategory.user_id))
                             .where(UserCategory.category_id == user_category.category_id)
                             .where(UserCategory.user_id != user_id))

        other_users_result = await session.execute(other_users_query)
        other_users_count = other_users_result.scalar()

        # Если категория не используется другими пользователями, добавляем её в список для удаления
        if other_users_count == 0:
            categories_to_delete.append(user_category.category_id)

        # Удаляем связь с UserCategory
        await session.delete(user_category)

    # 7. Удаляем уникальные категории
    for category_id in categories_to_delete:
        category_query = await session.get(Category, category_id)
        if category_query:
            await session.delete(category_query)

    # Завершаем транзакцию
    await session.commit()
    print(f"Данные пользователя с ID {user_id} успешно очищены.")


async def orm_get_user(session: AsyncSession, user_id: int):
    user = await session.get(User, user_id)
    return user


async def orm_get_user_wallets_all(session: AsyncSession, user_id: int):
    query = (
        select(Wallet)
        .where(and_(Wallet.user_id == user_id, Wallet.is_deleted == False))
        .options(
            selectinload(Wallet.currency),
            selectinload(Wallet.wallet_type),
            selectinload(Wallet.wallet_target),
            selectinload(Wallet.wallet_investment),
        )
    )
    result = await session.execute(query)
    wallets = result.scalars().all()
    return wallets

async def orm_get_user_wallets_not_zero(session: AsyncSession, user_id: int):
    query = (
        select(Wallet)
        .where(and_(Wallet.user_id == user_id,
                    Wallet.balance > 0,
                    Wallet.is_deleted == False))
        .options(
            selectinload(Wallet.wallet_type)
        )
    )
    result = await session.execute(query)
    wallets = result.scalars().all()

    # Определяем желаемый порядок типов
    order = {'Кошелёк': 0, 'Вклад': 1, 'Цель': 2}

    # Сортировка по ключу
    wallets.sort(key=lambda w: order.get(w.wallet_type.wallet_type_name, 99))

    return wallets


async def orm_get_user_wallets_without_one(session: AsyncSession, data: dict):
    query = (
        select(Wallet)
        .where(and_(Wallet.user_id == data['user_id'],
                    Wallet.wallet_id != data['wallet_id'],
                    Wallet.is_deleted == False))
        .options(
            selectinload(Wallet.wallet_type)
        )
    )
    result = await session.execute(query)
    wallets = result.scalars().all()

    # Определяем желаемый порядок типов
    order = {'Кошелёк': 0, 'Вклад': 1, 'Цель': 2}

    # Сортировка по ключу
    wallets.sort(key=lambda w: order.get(w.wallet_type.wallet_type_name, 99))

    return wallets

# async def orm_get_user_wallets_target(session: AsyncSession, data: dict):
#     query = (
#         select(Wallet)
#         .join(WalletTarget, WalletTarget.wallet_id == Wallet.wallet_id)
#         .where(and_(Wallet.user_id == data['user_id'],
#                     Wallet.wallet_id != data['wallet_id'],
#                     Wallet.is_deleted == False,
#                     WalletTarget.target_amount < Wallet.balance))
#     )
#     result = await session.execute(query)
#     wallets_tr = result.scalars().all()
#     return wallets_tr

async def orm_get_user_wallets(session: AsyncSession, data: dict):
    query = (
        select(Wallet).join(WalletType, WalletType.wallet_type_id == Wallet.wallet_type_id)
        .where(and_(Wallet.user_id == data['user_id'],
                    WalletType.wallet_type_name == data["wallet_type_name"],
                    Wallet.is_deleted == False
                    ))
    )

    result = await session.execute(query)
    wallets = result.scalars().all()
    return wallets

async def orm_get_user_wallet(session: AsyncSession, wallet_id: int):
    query = select(Wallet).where(Wallet.wallet_id == wallet_id)

    result = await session.execute(query)
    wallet = result.scalars().first()
    return wallet

async def orm_get_wallet_type_all(session:AsyncSession):
    query = select(WalletType)
    result = await session.execute(query)
    wallet_type = result.scalars().all()
    return wallet_type

async def orm_get_wallet_type_id(session: AsyncSession, type_name: str):
    query = (select(WalletType.wallet_type_id).where(WalletType.wallet_type_name == type_name))
    result = await session.execute(query)
    wallet_id = result.scalars().first()
    return wallet_id

async def orm_get_currency_id(session: AsyncSession, currency_code: str):
    query = (select(Currency.currency_id).where(Currency.currency_code == currency_code))
    result = await session.execute(query)
    currency_id = result.scalars().first()
    return currency_id

async def orm_add_wallet(session: AsyncSession, data: dict):
    if data.get('balance') is None:
        obj = Wallet(user_id=data['user_id'], wallet_type_id=data['wallet_type_id'],
                     wallet_name=data['wallet_name'],currency_id=data['currency_id'])
    else:
        obj = Wallet(user_id=data['user_id'], wallet_type_id=data['wallet_type_id'],
                     wallet_name=data['wallet_name'],currency_id=data['currency_id'],
                     balance=data['balance'])

    session.add(obj)
    await session.flush()
    await session.commit()
    return obj.wallet_id

async def orm_check_wallet_relationship(session: AsyncSession, wallet_id: int):
    used_in_transfer = await session.scalar(
        select(exists().where(
            (WalletTransfer.source_wallet_id == wallet_id) |
            (WalletTransfer.target_wallet_id == wallet_id)
        ))
    )

    used_in_transaction = await session.scalar(
        select(exists().where(CategoryTransaction.wallet_id == wallet_id))
    )

    used_in_recurring = await session.scalar(
        select(exists().where(RecurringPayment.wallet_id == wallet_id))
    )

    if used_in_recurring or used_in_transaction or used_in_transfer:
        return True
    return False



async def orm_delete_wallet(session: AsyncSession, wallet_id: int):
    used_in_transfer = await session.scalar(
        select(exists().where(
            (WalletTransfer.source_wallet_id == wallet_id) |
            (WalletTransfer.target_wallet_id == wallet_id)
        ))
    )

    used_in_transaction = await session.scalar(
        select(exists().where(CategoryTransaction.wallet_id == wallet_id))
    )

    used_in_recurring = await session.scalar(
        select(exists().where(RecurringPayment.wallet_id == wallet_id))
    )

    if used_in_transfer or used_in_transaction or used_in_recurring:
        query = (
                update(Wallet)
                .where(Wallet.wallet_id == wallet_id)
                .values(is_deleted=True)
        )
    else:
        query = (
            delete(Wallet)
            .where(Wallet.wallet_id == wallet_id)
        )

        await session.execute(
            delete(WalletTarget).where(WalletTarget.wallet_id == wallet_id)
        )
        await session.execute(
            delete(WalletInvestment).where(WalletInvestment.wallet_id == wallet_id)
        )
    await session.execute(query)
    await session.flush()
    await session.commit()

async def orm_add_wallet_target(session: AsyncSession, data: dict):
    query = insert(WalletTarget).values(wallet_id=data['wallet_id'],target_amount=data['target_amount'])
    await session.execute(query)
    await session.flush()
    await session.commit()

async def orm_add_wallet_investment(session: AsyncSession, data: dict):
    query = insert(WalletInvestment).values(wallet_id=data['wallet_id'],start_date=data['start_date'],
                                            end_date=data['end_date'],
                                            interest_rate=data['interest_rate'])
    await session.execute(query)
    await session.flush()
    await session.commit()


async def orm_update_wallet_balance(session: AsyncSession, data: dict):
    if data["cat_type"] == "Доход":
        query = (
            update(Wallet)
            .where(Wallet.wallet_id == data["wallet_id"])
            .values(balance=Wallet.balance + data["suma"])
        )
    else:
        query = (
            update(Wallet)
            .where(Wallet.wallet_id == data["wallet_id"])
            .values(balance=Wallet.balance - data["suma"])
        )
    await session.execute(query)
    await session.flush()
    await session.commit()

async def orm_update_wallet_name(session: AsyncSession, data: dict):
    query = (
             update(Wallet)
            .where(Wallet.wallet_id == data["wallet_id"])
            .values(wallet_name=data['wallet_name'])
    )
    await session.execute(query)
    await session.flush()
    await session.commit()

async def orm_update_wallet_target_amount(session: AsyncSession, data: dict):
    query = (
             update(WalletTarget)
            .where(WalletTarget.wallet_id == data["wallet_id"])
            .values(target_amount=data['target_amount'])
    )
    await session.execute(query)
    await session.flush()
    await session.commit()

async def orm_update_wallet_investment(session: AsyncSession, data: dict):

    match data['option']:
        case 'Изменить процентную ставку':
            query = (
                     update(WalletInvestment)
                    .where(WalletInvestment.wallet_id == data["wallet_id"])
                    .values(interest_rate=data['interest_rate'])
            )
        case 'Изменить дату открытия вклада':
            query = (
                update(WalletInvestment)
                .where(WalletInvestment.wallet_id == data["wallet_id"])
                .values(start_date=data['start_date'])
            )
        case 'Изменить дату закрытия вклада':
            query = (
                update(WalletInvestment)
                .where(WalletInvestment.wallet_id == data["wallet_id"])
                .values(end_date=data['end_date'])
            )
    await session.execute(query)
    await session.flush()
    await session.commit()

async def orm_check_unique_wallet_name(session: AsyncSession, data: dict):
    query = (
             select(Wallet)
            .join(WalletType, WalletType.wallet_type_id == Wallet.wallet_type_id)
            .where(and_(Wallet.user_id == data["user_id"],
                   Wallet.wallet_name == data['wallet_name'],
                   WalletType.wallet_type_name == data['wallet_type_name']))
    )
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_wallet(session: AsyncSession, data: dict):
    query = (
             select(Wallet)
            .join(WalletType, WalletType.wallet_type_id == Wallet.wallet_type_id)
            .where(and_(Wallet.user_id == data["user_id"],
                   Wallet.wallet_name == data['wallet_name'],
                   WalletType.wallet_type_name == data['wallet_type_name']))
    )
    result = await session.execute(query)
    return result.scalars().first()

async def orm_check_wallet_target(session: AsyncSession, data: dict):
    query = (
             select(WalletTarget)
            .where(WalletTarget.wallet_id == data['wallet_id'])
    )
    result = await session.execute(query)
    return result.scalars().first()

async def orm_check_wallet_investment(session: AsyncSession, data: dict):
    query = (
             select(WalletInvestment)
            .where(WalletInvestment.wallet_id == data['wallet_id'])
    )
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_category_types_id(session: AsyncSession, cat_type_name: str):
    query = select(CategoryType.category_type_id).where(CategoryType.category_type_name == cat_type_name)

    result = await session.execute(query)

    category_type = result.scalars().first()

    return category_type

async def orm_add_category(session: AsyncSession, data: dict):
    # Проверяем, существует ли уже такая категория
    query = select(Category).where(and_(Category.category_name == data['category_name'],Category.category_type_id == data['category_type_id']))
    result = await session.execute(query)
    category = result.scalars().first()
    # Если категории нет, создаём её
    if not category:
        category = Category(
            category_name=data['category_name'],
            category_type_id=data['category_type_id']
        )
        session.add(category)
        await session.commit()  # Сохраняем новую категорию, чтобы она получила id

    # Проверяем, есть ли уже связь этой категории с пользователем
    query = select(UserCategory).where(and_(UserCategory.user_id == data['user_id'],
                                            UserCategory.category_id == category.category_id))
    result = await session.execute(query)
    user_category = result.scalars().first()

    if user_category:
        if user_category.is_deleted:
            await session.execute(update(UserCategory).where(and_(UserCategory.user_id == data['user_id'],
                                            UserCategory.category_id == category.category_id))
                                  .values(is_deleted=False))
        else:
            return 'У вас уже есть такая категория с таким названием и типом'
    # Если связь не найдена, создаём её
    else:
        user_category = UserCategory(
            user_id=data['user_id'],
            category_id=category.category_id
        )
        session.add(user_category)

    # Коммитим изменения
    await session.flush()
    await session.commit()

async def orm_get_user_category(session: AsyncSession, data: dict):
    query = (
              select(Category)
             .join(UserCategory, UserCategory.category_id == Category.category_id)
              .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
             .where(and_(UserCategory.user_id == data["user_id"],
                         CategoryType.category_type_name == data["category_type_name"],
                         UserCategory.is_deleted == False))
    )

    result = await session.execute(query)
    user_cat = result.scalars().all()
    return user_cat



async def orm_add_default_categories(session: AsyncSession, user_id: int):
    default_categories = []

    income_cat_name = ['Прочее']
    expenses_cat_name = ['Прочее']

    income_cat_type_id = await orm_get_category_types_id(session, 'Доход')
    expenses_cat_type_id = await orm_get_category_types_id(session, 'Расход')

    for name in income_cat_name:
        default_categories.append({'category_name': name, 'category_type_id': income_cat_type_id,
                                   'user_id': user_id})

    for name in expenses_cat_name:
        default_categories.append({'category_name': name, 'category_type_id': expenses_cat_type_id,
                                   'user_id': user_id})

    for category_data in default_categories:
        await orm_add_category(session, category_data)

async def orm_add_default_wallet(session:AsyncSession, user_id: int):

    data_wallet = {
        'user_id': user_id,
        'wallet_type_name': 'Кошелёк',
        'wallet_type_id' : 1,
        "wallet_name": 'Базовый кошелёк',
        'currency_id': 3,
        'balance': 0
    }

    wallet = await orm_check_unique_wallet_name(session, data_wallet)

    check = False

    if wallet is not None and wallet.is_deleted == False:
        pass
    elif wallet is None:
        pass
    elif wallet.is_deleted:
        check = True

    if check:
        await orm_wallet_restore(session, data_wallet)
    else:
        await orm_add_wallet(session, data_wallet)


async def orm_add_category_transaction(session: AsyncSession, data: dict):
    obj = CategoryTransaction(category_id=data['category_id'],amount=data['suma'],wallet_id=data['wallet_id'])

    session.add(obj)
    await session.flush()
    await session.commit()

async def orm_get_category_transaction(session: AsyncSession, user_id: int, cat_type_name: str, *date):
    if not date:
        query = (
                    select(CategoryTransaction, Category.category_name, Wallet.wallet_name)
                    .join(Category, CategoryTransaction.category_id == Category.category_id)
                    .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
                    .join(UserCategory, and_(
                        UserCategory.category_id == CategoryTransaction.category_id,
                        UserCategory.user_id == user_id
                    ))
                    .join(Wallet, Wallet.wallet_id == CategoryTransaction.wallet_id)
                    .where(CategoryType.category_type_name == cat_type_name)
        )
    else:
        print(date)
        print(date[0][0],date[0][1])

        # ((datetime.datetime(2025, 5, 12, 0, 0), datetime.datetime(2025, 5, 13, 0, 0)),)
        # 2025 - 05 - 12 00: 00:00
        # 2025 - 05 - 13 00: 00:00
        query = (
                    select(CategoryTransaction, Category.category_name, Wallet.wallet_name)
                    .join(Category, CategoryTransaction.category_id == Category.category_id)
                    .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
                    .join(UserCategory, and_(
                        UserCategory.category_id == CategoryTransaction.category_id,
                        UserCategory.user_id == user_id
                    ))
                    .join(Wallet, Wallet.wallet_id == CategoryTransaction.wallet_id)
                    .where(and_(CategoryType.category_type_name == cat_type_name,
                                or_(CategoryTransaction.transaction_date >= date[0][0],
                                CategoryTransaction.transaction_date < date[0][1])
                                ))
        )

    cat_tr = await session.execute(query)
    res = cat_tr.all()
    return res


async def orm_get_category_transaction_for_budget(session: AsyncSession, user_id: int, cat_name: str, date):

    query = (
                    select(CategoryTransaction)
                    .join(Category, CategoryTransaction.category_id == Category.category_id)
                    .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
                    .join(UserCategory, and_(
                        UserCategory.category_id == CategoryTransaction.category_id,
                        UserCategory.user_id == user_id
                    ))
                    .where(and_(CategoryType.category_type_name == "Расход",
                                Category.category_name == cat_name,
                                date[0] <= CategoryTransaction.transaction_date,
                                CategoryTransaction.transaction_date < date[1])
                    )
        )

    cat_tr = await session.execute(query)
    res = cat_tr.all()
    return res

async def orm_get_user_budget(session: AsyncSession, user_id: int, *period_id):
    if period_id:
        query = (
                select(Budget, Category.category_name, Period.period_name)
                .join(Category, Category.category_id == Budget.category_id)
                .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
                .join(Period, Period.period_id == Budget.period_id)
                .where(and_(Budget.user_id == user_id, CategoryType.category_type_name == "Расход",
                            Period.period_id == period_id[0]))
                 )
    else:
        query = (
                select(Budget, Category.category_name, Period.period_name)
                .join(Category, Category.category_id == Budget.category_id)
                .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
                .join(Period, Period.period_id == Budget.period_id)
                .where(and_(Budget.user_id == user_id, CategoryType.category_type_name == "Расход"))
                 )

    user_budget = await session.execute(query)
    return user_budget.all()


async def orm_get_user_recurring_payment(session: AsyncSession, user_id: int, *period_id):
    if period_id:
        query = (
                select(RecurringPayment, Category.category_name, Period.period_name)
                .join(Category, Category.category_id == RecurringPayment.category_id)
                .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
                .join(Period, Period.period_id == RecurringPayment.period_id)
                .where(and_(RecurringPayment.user_id == user_id, CategoryType.category_type_name == "Расход",
                            Period.period_id == period_id[0]))
                 )
    else:
        query = (
                select(RecurringPayment, Category.category_name, Period.period_name)
                .join(Category, Category.category_id == RecurringPayment.category_id)
                .join(CategoryType, CategoryType.category_type_id == Category.category_type_id)
                .join(Period, Period.period_id == RecurringPayment.period_id)
                .where(and_(RecurringPayment.user_id == user_id, CategoryType.category_type_name == "Расход"))
                 )

    user_recurring_payment = await session.execute(query)
    return user_recurring_payment.all()


async def orm_get_wallet_transfer(session: AsyncSession, user_id: int):

    SourceWallet = aliased(Wallet)
    TargetWallet = aliased(Wallet)

    query = (
        select(
            WalletTransfer,
            SourceWallet.wallet_name.label("source_wallet_name"),
            TargetWallet.wallet_name.label("target_wallet_name")
        )
        .join(SourceWallet, SourceWallet.wallet_id == WalletTransfer.source_wallet_id)
        .join(TargetWallet, TargetWallet.wallet_id == WalletTransfer.target_wallet_id)
        .where(SourceWallet.user_id == user_id)
    )
    cat_tr = await session.execute(query)
    res = cat_tr.all()
    return res


async def orm_add_wallet_transfer(session: AsyncSession, data: dict):
    obj = WalletTransfer(source_wallet_id=data['source_wallet_id'],
                         amount=data['amount'],
                         target_wallet_id=data['target_wallet_id'])

    session.add(obj)
    await session.flush()
    await session.commit()


async def orm_wallet_restore(session: AsyncSession, data: dict):
    query = (
            update(Wallet)
            .where(and_(Wallet.wallet_name == data['wallet_name'],
                        Wallet.wallet_type_id == data['wallet_type_id'],
                        Wallet.user_id == data['user_id']))
            .values(is_deleted=False)
    )

    await session.execute(query)
    await session.flush()
    await session.commit()

async def orm_delete_category(session: AsyncSession, cat_id: int, user_id: int):
    used_in_transaction = await session.scalar(
        select(exists().where(CategoryTransaction.category_id == cat_id))
    )

    used_in_rec_pay = await session.scalar(
        select(exists().where(RecurringPayment.category_id == cat_id))
    )

    used_in_budget = await session.scalar(
        select(exists().where(Budget.category_id == cat_id))
    )

    used_other_users = await session.scalar(
        select(exists().where(and_(UserCategory.category_id == cat_id,
                                   UserCategory.user_id != user_id)))
    )

    if used_in_transaction or used_in_rec_pay or used_in_budget:
        query = (
            update(UserCategory)
            .where(and_(UserCategory.category_id == cat_id,
                        UserCategory.user_id == user_id))
            .values(is_deleted=True)
        )
    else:
        if used_other_users:
            query = (
                delete(UserCategory)
                .where(and_(UserCategory.category_id == cat_id,
                            UserCategory.user_id == user_id))
            )
        else:
            await session.execute(delete(Category).where(Category.category_id == cat_id))
            query = (
                delete(UserCategory)
                .where(and_(UserCategory.category_id == cat_id,
                            UserCategory.user_id == user_id))
            )
    await session.execute(query)
    await session.flush()
    await session.commit()


async def get_all_periods(session: AsyncSession):
    query = select(Period)

    periods = await session.execute(query)
    return periods.all()


async def get_period_id(session: AsyncSession, period_name: str):
    query = select(Period.period_id).where(Period.period_name == period_name)

    period_id = await session.execute(query)
    return period_id.scalars().first()


async def orm_add_budget(session: AsyncSession, user_id: int, data: dict):
    obj = Budget(user_id=user_id, category_id=data['add_budget_name_expenses'][1],
                 budget_limit=data['add_budget_amount_expenses'],
                 period_id=data['budget_period_expenses'][1])

    session.add(obj)
    await session.flush()
    await session.commit()


async def orm_delete_user_budget(session: AsyncSession, user_id: int, period_id: int, category_id: int):
    query = (
            delete(Budget)
            .where(and_(Budget.user_id == user_id,
                   Budget.period_id == period_id,
                   Budget.category_id == category_id)
             )
    )

    await session.execute(query)
    await session.flush()
    await session.commit()


async def orm_check_budget_limit(session: AsyncSession, data: dict):
    query = (
            select(Budget.budget_limit)
            .where(and_(Budget.user_id == data['user_id'],
                        Budget.period_id == data['period_id'],
                        Budget.category_id == data['category_id'])
                   )
    )

    res = await session.execute(query)
    return res.scalars().first()

async def orm_update_budget_limit(session: AsyncSession, data: dict):
    query = (
             update(Budget)
             .where(and_(Budget.user_id == data['user_id'],
                         Budget.period_id == data['period_id'],
                         Budget.category_id == data['category_id'])
                    )
            .values(budget_limit=data['budget_limit'])
    )
    await session.execute(query)
    await session.flush()
    await session.commit()
