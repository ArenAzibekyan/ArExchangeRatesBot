import requests
from bs4 import BeautifulSoup
import datetime


requestDate = datetime.date.today() - datetime.timedelta(days=10)
html = ''
ratesTable = {}


def getHtml():
    url = 'https://www.cbr.ru/currency_base/daily.aspx?date_req={0}.{1}.{2}'.format(requestDate.day, requestDate.month, requestDate.year)
    try:
        response = requests.get(url)
    except:
        return None
    else:
        return response.text


def getRatesTable():
    global requestDate, html, ratesTable
    localDate = datetime.date.today()
    if (localDate - requestDate).days > 1:
        requestDate = localDate - datetime.timedelta(days=1)
        html = getHtml()
        ratesTable = {}
        if html:
            soup = BeautifulSoup(html, 'lxml')
            soup = soup.find('table', class_='data')
            soup = soup.find_all('tr')
            soup.pop(0)
            for tr in soup:
                l = tr.get_text().split('\n')
                ratesTable[l[1]] = {'count': l[2], 'price': float(l[4].replace(',', '.'))}


def getRate(name):
    global ratesTable
    getRatesTable()
    return (ratesTable[name] if name in ratesTable else None)

