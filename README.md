# MoneyTracker – Telegram-бот для управления личными финансами


## 📌 Основные возможности:
- Добавление доходов и расходов
- Поддержка нескольких кошельков
- Категоризация транзакций
- Финансовые отчёты и графики
- Экспорт данных
- Назначение лимитов и регулярных платежей
- Переводы между кошельками
- Конвертация валют и расчёт вклада
- Прогнозирование финансовых показателей


## 🚀 Установка и запуск

1. **Клонируйте репозиторий:**

```bash
git clone https://github.com/0SmasH0/tg-bot-MoneyTracker.git
cd moneytracker-bot
```

2. **Создайте файл `.env` в корне проекта** и укажите в нём:

```env
TOKEN=ваш_токен_бота
DB_LITE=sqlite+aiosqlite:///путь_к_вашей_базе.db
```

> 🔑 `TOKEN` — можно получить у [@BotFather](https://t.me/BotFather) в Telegram
> 📂 `DB_LITE` — строка подключения к SQLite (используется `aiosqlite`)

Пример:

```env
TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
DB_LITE=sqlite+aiosqlite:///moneytracker.sqlite
```

3. **Установите зависимости:**

```bash
pip install -r requirements.txt
```

4. **Запустите бота:**

```bash
python app.py
```
