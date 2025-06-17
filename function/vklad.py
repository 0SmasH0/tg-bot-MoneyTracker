import requests
from bs4 import BeautifulSoup

url = 'https://myfin.by/vklady?sort=-rate'



data = requests.get(url)
soap = BeautifulSoup(data.text,'html.parser')
proc_day = soap.findAll('div', class_="products__product-accent",limit=20)
b = [i.text.strip().replace('  ','') for i in proc_day]
name_bank = soap.findAll('div',class_='products__product-bank-name',limit=10)
name_vklad = soap.findAll('div', class_='products__product-product-name', limit=10)
nb = [i.text for i in name_bank]
nv = [i.text for i in name_vklad]

print(b,nb,nv,sep='\n')
