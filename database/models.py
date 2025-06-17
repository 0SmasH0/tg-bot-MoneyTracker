from datetime import datetime

from sqlalchemy import (
    String, Text, Date, DateTime, Integer, BigInteger, Boolean, DECIMAL,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(130), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    wallet = relationship('Wallet', back_populates='user')
    user_categories = relationship('UserCategory', back_populates='user')
    budgets = relationship('Budget', back_populates='user')
    recurring_payments = relationship('RecurringPayment', back_populates='user')


class Currency(Base):
    __tablename__ = 'currency'

    currency_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    currency_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    currency_fullname: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    wallet = relationship('Wallet', back_populates='currency')


class CategoryType(Base):
    __tablename__ = 'category_types'

    category_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_type_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    categories = relationship('Category', back_populates='category_type')


class Category(Base):
    __tablename__ = 'category'
    __table_args__ = (UniqueConstraint('category_name', 'category_type_id'),)

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type_id: Mapped[int] = mapped_column(ForeignKey('category_types.category_type_id', ondelete='RESTRICT'))

    category_type = relationship('CategoryType', back_populates='categories')
    user_categories = relationship('UserCategory', back_populates='category')
    category_transactions = relationship('CategoryTransaction', back_populates='category')
    budgets = relationship('Budget', back_populates='category')
    recurring_payments = relationship('RecurringPayment', back_populates='category')


class UserCategory(Base):
    __tablename__ = 'user_category'
    __table_args__ = (UniqueConstraint('category_id', 'user_id'),)

    category_id: Mapped[int] = mapped_column(ForeignKey('category.category_id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user = relationship('User', back_populates='user_categories')
    category = relationship('Category', back_populates='user_categories')


class WalletType(Base):
    __tablename__ = 'wallet_type'

    wallet_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_type_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    wallet = relationship('Wallet', back_populates='wallet_type')


class Wallet(Base):
    __tablename__ = 'wallet'

    wallet_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'))
    wallet_type_id: Mapped[int] = mapped_column(ForeignKey('wallet_type.wallet_type_id', ondelete='RESTRICT'))
    wallet_name: Mapped[str] = mapped_column(String(30), nullable=False)
    currency_id: Mapped[int] = mapped_column(ForeignKey('currency.currency_id', ondelete='RESTRICT'))
    balance: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False,  index=True)

    outgoing_transfers = relationship('WalletTransfer', foreign_keys='WalletTransfer.source_wallet_id', back_populates='source_wallet')
    incoming_transfers = relationship('WalletTransfer', foreign_keys='WalletTransfer.target_wallet_id', back_populates='target_wallet')
    category_transactions = relationship('CategoryTransaction', back_populates='wallet')

    # Остальные связи без изменений
    user = relationship('User', back_populates='wallet')
    currency = relationship('Currency', back_populates='wallet')
    wallet_type = relationship('WalletType', back_populates='wallet')
    wallet_target = relationship('WalletTarget', uselist=False, back_populates='wallet')
    wallet_investment = relationship('WalletInvestment', uselist=False, back_populates='wallet')


class WalletTarget(Base):
    __tablename__ = 'wallet_target'

    wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.wallet_id', ondelete='RESTRICT'), primary_key=True)
    target_amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=True)

    wallet = relationship('Wallet', back_populates='wallet_target')

class WalletInvestment(Base):
    __tablename__ = 'wallet_investment'

    wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.wallet_id', ondelete='RESTRICT'), primary_key=True)
    start_date: Mapped[Date] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date] = mapped_column(Date, nullable=True)
    interest_rate: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)

    wallet = relationship('Wallet', back_populates='wallet_investment')


class WalletTransfer(Base):
    __tablename__ = 'wallet_transfer'

    transfer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.wallet_id', ondelete='RESTRICT'))
    target_wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.wallet_id', ondelete='RESTRICT'))
    amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    transfer_date: Mapped[Date] = mapped_column(DateTime, default=func.current_date())

    source_wallet = relationship('Wallet', foreign_keys=[source_wallet_id], back_populates='outgoing_transfers')
    target_wallet = relationship('Wallet', foreign_keys=[target_wallet_id], back_populates='incoming_transfers')

class CategoryTransaction(Base):
    __tablename__ = 'category_transaction'

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.wallet_id', ondelete='RESTRICT'))
    amount: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey('category.category_id', ondelete='RESTRICT'))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    wallet = relationship('Wallet', back_populates='category_transactions')
    category = relationship('Category', back_populates='category_transactions')


## время +3 надо

class Period(Base):
    __tablename__ = 'periods'

    period_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_name: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)

    budgets = relationship('Budget', back_populates='period')
    recurring_payments = relationship('RecurringPayment', back_populates='period')


class Budget(Base):
    __tablename__ = 'budgets'
    __table_args__ = (UniqueConstraint('user_id', 'category_id', 'period_id'),)

    budget_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'))
    category_id: Mapped[int] = mapped_column(ForeignKey('category.category_id', ondelete='RESTRICT'))
    budget_limit: Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    current_spent: Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)
    period_id: Mapped[int] = mapped_column(ForeignKey('periods.period_id', ondelete='RESTRICT'))
    created_at: Mapped[Date] = mapped_column(Date, default=func.current_date())

    user = relationship('User', back_populates='budgets')
    category = relationship('Category', back_populates='budgets')
    period = relationship('Period', back_populates='budgets')


class RecurringPayment(Base):
    __tablename__ = 'recurring_payments'

    recurring_payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # wallet_id: Mapped[int] = mapped_column(ForeignKey('wallet.wallet_id', ondelete='RESTRICT'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'))

    planned_amount : Mapped[float] = mapped_column(DECIMAL(15, 2), nullable=False)
    current_amount : Mapped[float] = mapped_column(DECIMAL(15, 2), default=0)

    category_id: Mapped[int] = mapped_column(ForeignKey('category.category_id', ondelete='RESTRICT'))
    next_payment_date: Mapped[Date] = mapped_column(Date, nullable=False)
    period_id: Mapped[int] = mapped_column(ForeignKey('periods.period_id', ondelete='RESTRICT'))
    created_at: Mapped[Date] = mapped_column(Date, default=func.current_date())

    # wallet = relationship('Wallet', back_populates='recurring_payments')
    user = relationship('User', back_populates='recurring_payments')
    category = relationship('Category', back_populates='recurring_payments')
    period = relationship('Period', back_populates='recurring_payments')
