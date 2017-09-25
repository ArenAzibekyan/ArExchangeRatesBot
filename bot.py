import requests
import threading
import yobit
import centralBank
import myToken


URL = 'https://api.telegram.org/bot' + myToken.__get__() + '/'
updateId = 0
helpCryptoDict = {'/btc': 'Курс Биткойна к Доллару США',
                  '/eth': 'Курс Эфириума к Доллару США', }
helpCurrencyDict = {'/btc': 'Курс Биткойна к Доллару США',
                    '/eth': 'Курс Эфириума к Доллару США',
                    '/aud': 'Курс Австралийского доллара',
                    '/azn': 'Курс Азербайджанского маната',
                    '/amd': 'Курс Армянских драмов',
                    '/byn': 'Курс Белорусского рубля',
                    '/bgn': 'Курс Болгарского льва',
                    '/brl': 'Курс Бразильского реала',
                    '/huf': 'Курс Венгерских форинтов',
                    '/krw': 'Курс Вон Республики Корея',
                    '/hkd': 'Курс Гонконгских долларов',
                    '/dkk': 'Курс Датских крон',
                    '/usd': 'Курс Доллара США',
                    '/eur': 'Курс Евро',
                    '/inr': 'Курс Индийских рупий',
                    '/kzt': 'Курс Казахстанских тенге',
                    '/cad': 'Курс Канадского доллара',
                    '/kgs': 'Курс Киргизских сомов',
                    '/cny': 'Курс Китайских юаней',
                    '/mdl': 'Курс Молдавских леев',
                    '/tmt': 'Курс Нового туркменского маната',
                    '/nok': 'Курс Норвежских крон',
                    '/pln': 'Курс Польских злотых',
                    '/ron': 'Курс Румынского лея',
                    '/xdr': 'Курс СДР (специальных прав заимствования)',
                    '/sgd': 'Курс Сингапурского доллара',
                    '/tjs': 'Курс Таджикских сомони',
                    '/try': 'Курс Турецких лир',
                    '/uzs': 'Курс Узбекских сумов',
                    '/uah': 'Курс Украинских гривен',
                    '/gbp': 'Курс Фунт стерлингов',
                    '/czk': 'Курс Чешских крон',
                    '/sek': 'Курс Шведских крон',
                    '/chf': 'Курс Швейцарских франков',
                    '/zar': 'Курс Южноафриканских рэндов',
                    '/jpy': 'Курс Японских иен'}
helpMes = '*Криптовалюты:*\n'
helpMes += '\n'.join([key + ' - к' + helpCryptoDict[key][1:] for key in sorted(helpCryptoDict)])
helpMes += '\n*Курсы ЦБ:*\n'
helpMes += '\n'.join([key + ' - к' + helpCurrencyDict[key][1:] for key in sorted(helpCurrencyDict)])
startMes = 'Здравствуйте! Я позволяю смотреть официальные курсы Центробанка для всех валют к Российскому рублю, а также курсы двух популярнейших криптовалют прямиком из биржи. Для получения полного списка команд воспользуйтесь командой /help'


def getUpdates():
    url = URL + 'getUpdates?timeout=10'
    if updateId > 0:
        url += '&offset=' + str(updateId)
    try:
        response = requests.get(url)
    except:
        return None
    else:
        return response.json()


def getNewMessages():
    data = getUpdates()
    if data:
        if not data['ok'] == True:
            return None
        elif not len(data['result']):
            return None
        else:
            data = data['result']
            for mes in data:
                if 'edited_message' in mes:
                    mes['message'] = mes['edited_message']
                    del mes['edited_message']
            mesList = [{'updateId': mes['update_id'],
                        'chatId': mes['message']['chat']['id'],
                        'chatType': mes['message']['chat']['type'],
                        'mesId': mes['message']['message_id'],
                        'mesText': mes['message']['text']}
                       for mes in data if 'message' in mes if 'text' in mes['message']]
            return mesList
    else:
        return None


def sendMessage(chatId, mesText, replyId = -1, parseMode = 'Markdown'):
    url = URL + 'sendMessage?chat_id={0}&text={1}&parse_mode={2}'.format(chatId, mesText, parseMode)
    if not replyId == -1: url += '&reply_to_message_id={}'.format(replyId)
    try:
        response = requests.get(url)
    except:
        return None
    else:
        return response.json()


def responseCrypto(mes):
    mesText = mes['mesText']
    respMes = '`' + helpCryptoDict[mesText] + '`\n('
    mesText = mesText[1:]
    rates = yobit.cry_usd(mesText)
    if rates:
        respMes += mesText.upper() + ' -> USD)\n*Avg:* _{2:.2f}_\n*Min:* _{0:.2f}_\n*Max:* _{1:.2f}_'.format(*rates)
        sendMessage(mes['chatId'], respMes, (mes['mesId'] if mes['chatType'] == 'group' else -1))


def responseCurrency(mes):
    mesText = mes['mesText']
    if mesText in helpCurrencyDict:
        respMes = '`' + helpCurrencyDict[mesText] + ' к Российскому рублю`\n('
        mesText = mesText[1:].upper()
        rate = centralBank.getRate(mesText)
        if rate:
            if not rate['count'] == '1':
                respMes += rate['count'] + ' '
            respMes += mesText + ' -> RUB)\n*ЦБ:* _{0:.2f}_'.format(rate['price'])
            sendMessage(mes['chatId'], respMes, (mes['mesId'] if mes['chatType'] == 'group' else -1))


if __name__ == '__main__':
    while True:
        mesList = getNewMessages()
        print(mesList)
        if mesList:
            for mes in mesList:
                mesText = mes['mesText']
                if '@' in mesText:
                    spl = mesText.split('@')
                    if not spl[1] == 'ArExchangeRatesBot':
                        continue
                    else:
                        mes['mesText'] = mesText = spl[0]
                if mesText[0] == '/':
                    if mesText == '/start':
                        sendMessage(mes['chatId'], startMes)
                        sendMessage(mes['chatId'], '*Приятного пользования!*')
                    elif mesText == '/help':
                        sendMessage(mes['chatId'], helpMes, (mes['mesId'] if mes['chatType'] == 'group' else -1))
                    elif mesText == '/btc' or mesText == '/eth':
                        threading.Thread(target=responseCrypto, args=(mes,)).start()
                    else:
                        threading.Thread(target=responseCurrency, args=(mes,)).start()
            updateId = mesList[-1]['updateId'] + 1

