import io

import soundfile as sf
import speech_recognition as sr
import re

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_user_category, orm_get_user_wallets_all, orm_update_wallet_balance, \
    orm_add_category_transaction


async def work_with_voice_text(session: AsyncSession, user_id: int, text: str) -> dict | str:
    data = text.lower()
    print(1, data)
    in_or_ex = 'расход|доход'

    incomes_expenses = re.findall(fr'\b({in_or_ex})', data)

    print(2, incomes_expenses)
    if not incomes_expenses:
        return 'Вы не указали доход это или расход'

    suma = re.findall(r'\b\d+\.?\d*\b', data)
    print(3, suma)
    if not suma:
        return 'Вы не указали сумму'

    cat_info = {"user_id": user_id, "category_type_name": incomes_expenses[0].title()}

    cats = await orm_get_user_category(session, cat_info)

    categories = '|'.join([cat.category_name[:5] if len(cat.category_name) > 4 else cat.category_name for cat in cats]).lower()

    result = {'suma': suma, 'in_or_ex': incomes_expenses[0].title()}

    cat = re.findall(fr'\b({categories})', data)
    if not cat:
        return 'Вы неверно указали категорию'

    id_cat = categories.split('|').index(cat[0])
    result['cat'] = cats[id_cat].category_id

    user_wallets = await orm_get_user_wallets_all(session, user_id)

    wallets = '|'.join([wal.wallet_name[:5] if len(wal.wallet_name) > 6 else wal.wallet_name for wal in user_wallets]).lower()
    print(123,wallets)
    wal = re.findall(fr'\b({wallets})', data)
    print(11, wal)
    if not wal:
        return 'Вы неверно указали кошелёк'

    id_wal = wallets.split('|').index(wal[0])
    result['wal'] = user_wallets[id_wal].wallet_id
    print(result)
    return result





def ogg_to_wav(voice_io: io.BytesIO) -> io.BytesIO:
    data, samplerate = sf.read(voice_io)

    wav_io = io.BytesIO()
    sf.write(wav_io, data, samplerate, format='WAV')
    wav_io.seek(0)

    return wav_io


def voice_to_text(voice_io: io.BytesIO) -> str | bool:
    wav_io = ogg_to_wav(voice_io)

    recognizer = sr.Recognizer()

    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio_data, language='ru-RU')
            return text

        except sr.UnknownValueError:
            return False


async def voice_result(session: AsyncSession, data: dict | str, user_id: int) -> str:
    if not isinstance(data, str):
        data['suma'][0] = data['suma'][0].replace('.', '')

        if len(data['suma'][-1]) == 1:
            data['suma'][1] = '0' + data['suma'][1]

            suma = float(''.join(data['suma'][:-1]) + f'.{data['suma'][-1]}')
        else:
            suma = float(data['suma'][0].replace('.', ''))

        result = {'suma': suma, 'category_id': data['cat'], "wallet_id": data["wal"],"cat_type": data["in_or_ex"]}

        await orm_update_wallet_balance(session, result)
        await orm_add_category_transaction(session,result)

        return 'Успешно добавлено'

    else:
        return data
