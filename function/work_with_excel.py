import pandas as pd
import io
import xlsxwriter
from datetime import datetime

def create_data_for_sheet(data: list, operation_type: str):
    if operation_type == 'Переводы':
        data_for_sheet = pd.DataFrame({
            'Дата': [date[0].transfer_date.strftime("%d.%m.%Y") for date in data],
            'Сумма (BYN)': [suma[0].amount for suma in data],
            'Кошелёк №1 (с какого)': [wallet[1] for wallet in data],
            'Кошелёк №2 (куда)': [wallet[2] for wallet in data]
        })
    else:
        data_for_sheet = pd.DataFrame({
            'Дата': [date[0].transaction_date.strftime("%d.%m.%Y") for date in data],
            'Сумма (BYN)': [suma[0].amount for suma in data],
            'Категория': [cat[1] for cat in data],
            'Кошелёк': [wallet[2] for wallet in data]
        })

    return data_for_sheet


def data_in_excel(data_income: list, data_expenses: list, data_transfer: list):

    incomes = create_data_for_sheet(data_income, 'Доходы')
    expenses = create_data_for_sheet(data_expenses, 'Расходы')
    transfers = create_data_for_sheet(data_transfer, 'Переводы')

    # Словарь с листами Excel
    sheets_finance = {'Доходы': incomes, 'Расходы': expenses, 'Переводы': transfers}

    # Создаем объект памяти BytesIO
    xlsx_bytes = io.BytesIO()

    # Используем ExcelWriter с BytesIO как файл
    with pd.ExcelWriter(xlsx_bytes, engine='xlsxwriter') as writer:
        workbook = writer.book

        # 1. Формат для ячеек с границами и центровкой
        cell_format  = workbook.add_format({
            'border': 1,  # Границы со всех сторон
            'align': 'center',
            'valign': 'vcenter'
        })

        # 2. Формат для шапки (жирный шрифт + голубая заливка)
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4285f4',  # Голубой цвет
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            "font_size": 15
        })

        # Проходим по каждому листу и добавляем данные
        for sheet_name, df in sheets_finance.items():
            # Записываем DataFrame без индекса
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
            worksheet = writer.sheets[sheet_name]

            # Записываем заголовки вручную с нужным форматом
            for col_num, column_name in enumerate(df.columns):
                worksheet.write(0, col_num, column_name, header_format)

            # Применяем формат ко всем ячейкам с данными
            for row in range(1, len(df) + 1):  # Строки (начиная с 1, т.к. 0 — заголовки)
                for col in range(0, len(df.columns)):  # Столбцы (0, 1, 2, 3)
                    worksheet.write(row, col, df.iloc[row - 1, col], cell_format)

            match sheet_name:
                case 'Переводы':
                    worksheet.set_column('A:A', 15)  # Дата
                    worksheet.set_column('B:B', 25)  # Сумма
                    worksheet.set_column('C:C', 40)  # Категория
                    worksheet.set_column('D:D', 40)  # Кошелёк
                case _:
                    # Настройка ширины столбцов
                    worksheet.set_column('A:A', 15)  # Дата
                    worksheet.set_column('B:B', 25)  # Сумма
                    worksheet.set_column('C:C', 20)  # Категория
                    worksheet.set_column('D:D', 20)  # Кошелёк



    # Перемещаем указатель в начало, чтобы подготовить данные для чтения
    xlsx_bytes.seek(0)

    # Возвращаем байты файла Excel
    return xlsx_bytes
