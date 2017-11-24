import requests
from bs4 import BeautifulSoup
import datetime
from dateutil import relativedelta as rd
import matplotlib as mpl
mpl.use('Agg')
from matplotlib import pyplot as plt
import io
import json


#
# класс всего и вся
class CentralBankParser:
    #
    # конструктор
    def __init__(self):
        self.currencyTable = {}
        self.requestDate = datetime.date.min
        self.updateCurrencyTable()
    #
    # DD/MM/YYYY для сервера ЦБ
    def dateForServer(self, d):
        return d.strftime('%d/%m/%Y')
    #
    # обновление несвежей таблицы
    def checkRequestDate(self):
        if self.requestDate != datetime.date.today():
            self.updateCurrencyTable()
    #
    # список доступных валют
    def getAllMes(self):
        d = self.currencyTable
        l = ['/' + cur.lower() + ' - ' + str(d[cur]['nominal']) + ' ' + d[cur]['name'] for cur in d]
        mes = '*Список всех доступных валют:*\n'
        mes += '\n'.join(l)
        return mes
    #
    # инструкция
    @staticmethod
    def getHelpList():
        l = []
        # просмотреть курс
        mes = ''
        mes += '*Просмотреть курс валют*:\n'
        mes += '`——————\n/<xxx>\n——————`\n'
        mes += 'где <xxx> - трехбуквенный код валюты\n'
        mes += '/all - список всех доступных валют\n'
        mes += '_Примеры_:\n'
        mes += '`/usd` - курс Доллара США\n'
        mes += '`/eur` - курс Евро'
        l.append(mes)
        # конвертировать
        mes = ''
        mes += '*Конвертировать валюты*:\n'
        mes += '`————————————————————————\n/convert <c> <xxx> <yyy>\n————————————————————————`\n'
        mes += 'перевести <c> единиц валюты <xxx> в валюту <yyy>\n'
        mes += '<c> - положительное целое число\n'
        mes += '_Примеры_:\n'
        mes += '`/convert 100 usd rub` - 100 Долларов США в рубли\n'
        mes += '`/convert 100 rub usd` - 100 рублей в Доллары США\n'
        mes += '`/convert 100 usd eur` - 100 Долларов США в Евро'
        l.append(mes)
        # построить график
        mes = ''
        mes += '*Построить динамику котировок*:\n'
        mes += '`————————————————\n/<xxx> <c><time>\n————————————————`\n'
        mes += 'график за <c> временных интервалов <time>\n'
        mes += '<c> - положительное целое число\n'
        mes += '<time> принадлежит множеству (d, w, m, y)\n'
        mes += 'где d - день, w - неделя, m - месяц, y - год\n'
        mes += '_Примеры_:\n'
        mes += '`/usd 10d` - Доллара США за 10 дней\n'
        mes += '`/usd 2w` - за 2 недели\n'
        mes += '`/usd 3m` - за 3 месяца\n'
        mes += '`/usd 5y` - за 5 лет'
        l.append(mes)
        helpList = []
        for i in range(3):
            leftBtn = {'text': '<<<',
                       'callback_data': i - 1}
            if leftBtn['callback_data'] == -1:
                leftBtn['callback_data'] = 2
            rightBtn = {'text': '>>>',
                        'callback_data': i + 1}
            if rightBtn['callback_data'] == 3:
                rightBtn['callback_data'] = 0
            btns = [[leftBtn, rightBtn]]
            markup = {'reply_markup': json.dumps({'inline_keyboard': btns})}
            helpList.append({
                'text': l[i],
                'markup': markup
            })
        return helpList
    #
    # полное обновление таблицы валют
    def updateCurrencyTable(self):
        today = datetime.date.today()
        url = 'http://www.cbr.ru/scripts/XML_daily.asp?date_req='
        url += self.dateForServer(today)
        # get-запрос
        try:
            response = requests.get(url)
            response.encoding = 'windows-1251'
            response = response.text
        # не удался
        except:
            print('Exception:request in updateCurrencyTable method')
            self.currencyTable = {}
            self.requestDate = datetime.date.min
        # удался
        else:
            # парсинг
            try:
                result = {}
                soup = BeautifulSoup(response, 'lxml')
                # массив валют
                soup = soup.find_all('valute')
                # составление словаря в цикле
                for v in soup:
                    result[v.find('charcode').string.strip()] = {
                        'name': v.find('name').string.strip(),
                        'value': float(v.find('value').string.strip().replace(',', '.')),
                        'nominal': int(v.find('nominal').string.strip()),
                        'id': v.attrs['id'][0:6]
                    }
            # не удался
            except:
                print('Exception:parsing in updateCurrencyTable method')
                self.currencyTable = {}
                self.requestDate = datetime.date.min
            # удался
            else:
                self.currencyTable = result
                self.requestDate = today
    #
    # получение динамики котировок
    def getPlotData(self, curId, fromDate):
        # даты для сервера ЦБ
        fromDate = self.dateForServer(fromDate)
        toDate = self.dateForServer(datetime.date.today())
        # создание урлы
        url = 'http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1='
        url += fromDate + '&date_req2=' + toDate + '&VAL_NM_RQ=' + curId
        # get-запрос
        try:
            response = requests.get(url)
            response.encoding = 'windows-1251'
            response = response.text
        # не удался
        except:
            print('Exception:request in getPlotData method')
            return [], []
        # удался
        else:
            # парсинг
            try:
                soup = BeautifulSoup(response, 'lxml')
                soup = soup.find_all('record')
                # данные по оси абсцисс
                x = [datetime.date(int(d[-1]), int(d[1]), int(d[0])) for d in
                     [v.attrs['date'].split('.') for v in soup]]
                # данные по оси ординат
                finalNominal = int(soup[-1].find('nominal').string.strip())
                ratios = [finalNominal / int(r.find('nominal').string.strip()) for r in soup]
                y = [r * float(v.find('value').string.strip().replace(',', '.')) for v, r in zip(soup, ratios)]
            # не удался
            except:
                print('Exception:parsing in getPlotData method')
                return [], []
            # удался
            else:
                return x, y
    #
    # построение диаграммы
    def getImage(self, charcode, fromDate):
        currency = self.currencyTable[charcode]
        # запрос
        x, y = self.getPlotData(currency['id'], fromDate)
        # не удался
        if not x or not y:
            return None
        # удался
        title = 'Цена на ' + str(currency['nominal']) + ' ' + currency['name']
        title += '. Динамика котировок от ' + self.dateForServer(fromDate)
        # построение
        try:
            # построение
            fig = plt.figure(figsize=(9.6, 5.4), dpi=200)
            ax = fig.add_subplot(111)
            ax.plot(x, y)
            ax.set(title=title)
            ax.grid(True, which='both', color='0.9')
            ax.xaxis.set_major_formatter(mpl.dates.DateFormatter('%d/%m/%Y'))
            fig.autofmt_xdate()
            fig.tight_layout()
            # бинарный поток ввода-вывода в RAM
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            plt.close(fig)
            # чтение в битовый массив
            image = buf.getvalue()
            buf.close()
        # не удалось
        except:
            print('Exception in getImage method')
            return None
        # удалось
        else:
            return image
    #
    # обрабатывает поступившую команду
    def parseMesText(self, mesText):
        # только команда боту
        if mesText[0] != '/':
            return None
        mesText = mesText.split()
        command = mesText[0]
        # прямое обращение к боту
        if '@' in command:
            command = command.split('@')
            if not 'ArExchangeRatesBot' in command[1:]:
                return None
            command = command[0]
        command = command[1:].upper()
        # проверка свежести таблицы
        self.checkRequestDate()
        if not self.currencyTable:
            return None
        # наличие полученной команды
        if not command in self.currencyTable:
            # конвертация
            if command == 'CONVERT':
                params = mesText[1:]
                if len(params) < 3:
                    return {'ok': False,
                            'page': 1}
                amount, fromCur, toCur = params[:3]
                try:
                    amount = int(amount)
                except:
                    return {'ok': False,
                            'page': 1}
                else:
                    if amount > 0:
                        if fromCur == toCur:
                            return {'ok': False,
                                    'page': 1}
                        fromCur = fromCur.upper()
                        if not (fromCur == 'RUB' or fromCur in self.currencyTable):
                            return {'ok': False,
                                    'page': 1}
                        toCur = toCur.upper()
                        if not (toCur == 'RUB' or toCur in self.currencyTable):
                            return {'ok': False,
                                    'page': 1}
                        return {'ok': True,
                                'type': 'convert',
                                'amount': amount,
                                'from': fromCur,
                                'to': toCur}
                    else:
                        return {'ok': False,
                                'page': 1}
            elif command == 'START':
                return {'ok': True,
                        'type': 'start'}
            elif command == 'HELP':
                return {'ok': False,
                        'page': 0}
            elif command == 'ALL':
                return {'ok': True,
                        'type': 'all'}
            else:
                return None
        # с командой все, теперь параметр
        param = mesText[1:]
        # нет параметра
        if not param:
            return {'ok': True,
                    'type': 'cost',
                    'cur': command}
        param = param[0]
        if len(param) < 2:
            return {'ok': False,
                    'page': 2}
        last = param[-1]
        # не нужные параметры
        if not last in ('d', 'w', 'm', 'y'):
            return {'ok': False,
                    'page': 2}
        # оставшиеся символы кроме последнего
        param = param[:-1]
        try:
            param = int(param)
        except:
            return {'ok': False,
                    'page': 2}
        else:
            if param > 0:
                # графики менее чем за 5 дней запрещены
                if last == 'd' and param < 5:
                    return {'ok': False,
                            'page': 2}
                fromDate = datetime.date.today()
                # подсчет дельты времени
                if last == 'd':
                    delta = rd.relativedelta(days=param)
                elif last == 'w':
                    delta = rd.relativedelta(weeks=param)
                elif last == 'm':
                    delta = rd.relativedelta(months=param)
                else:
                    delta = rd.relativedelta(years=param)
                fromDate = fromDate - delta
                return {'ok': True,
                        'type': 'graph',
                        'cur': command,
                        'fromDate': fromDate}
            else:
                return {'ok': False,
                        'page': 2}