import requests

valuta = {'usd': 840, 'eur': 978, 'rub': 643,
          'pln': 985, 'cny': 156}

byn = {'Cur_Scale': 1, 'Cur_OfficialRate': 1}


def download_data(num: int) -> dict:
    values = eval(requests.get(f'https://api.nbrb.by/exrates/rates/{num}?parammode=1').text)
    return values


def conversion(suma: float | int, id_val: str, id_val_wish: str) -> float:

    if id_val != 'byn':
        curs_info = download_data(valuta.get(id_val))
    else:
        curs_info = byn

    if id_val_wish != 'byn':
        curs_info_2 = download_data(valuta.get(id_val_wish))
    else:
        curs_info_2 = byn

    if curs_info_2['Cur_Scale'] != 1:
        curs_info_2['Cur_OfficialRate'] /= curs_info_2['Cur_Scale']

    return round(((suma / curs_info['Cur_Scale'] * curs_info['Cur_OfficialRate']) / curs_info_2['Cur_OfficialRate']), 2)
