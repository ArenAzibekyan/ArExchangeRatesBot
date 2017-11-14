import requests
from time import sleep
from centralBankParser import CentralBankParser
import myToken


URL = 'https://api.telegram.org/bot' + myToken.get() + '/'
updateId = 0


#
# получение обновлений
def getUpdates():
    # урла
    url = URL + 'getUpdates?timeout=10'
    # только новые апдейты
    if updateId > 0:
        url += '&offset=' + str(updateId)
    # get-запрос
    try:
        response = requests.get(url).json()
    # не удался
    except:
        print('Exception in getUpdates method')
        sleep(10)
        return None
    # удался
    else:
        return response


#
# получение новых сообщений
def getNecessaryUpd():
    updates = getUpdates()
    # запрос удался
    if updates:
        # все ок
        if not updates['ok']:
            return None
        updates = updates['result']
        # есть ли апдейты
        if not len(updates):
            return None
        # сохранение айди апдейта
        global updateId
        updateId = updates[-1]['update_id'] + 1
        # избавление от редактированных сообщений
        for upd in updates:
            if 'edited_message' in upd:
                upd['message'] = upd['edited_message']
        # только текстовые сообщения и нажатия кнопок
        necessary = [upd for upd in updates if ('message' in upd and 'text' in upd['message']) or 'callback_query' in upd]
        return necessary


#
# отправка сообщения
def sendMessage(chatId, mesText, replyMarkup=None, parseMode='Markdown'):
    url = URL + 'sendMessage?chat_id={0}&text={1}&parse_mode={2}'.format(chatId, mesText, parseMode)
    # get-запрос
    try:
        if replyMarkup:
            response = requests.get(url, data=replyMarkup)
        else:
            response = requests.get(url)
        response = response.json()
    # не удался
    except:
        print('Exception in sendMessage method')
        return None
    # удался
    else:
        return response


#
# отправка фотки
def sendPhoto(chatId, image):
    # урла
    url = URL + 'sendPhoto'
    # данные запроса
    data = {'chat_id': chatId}
    file = {'photo': image}
    # get-запрос
    try:
        response = requests.post(url, files=file, data=data).json()
    # не удался
    except:
        print('Exception in sendPhoto method')
        return None
    # удался
    else:
        return response


#
# редактирование сообщения
def editMessage(chatId, mesId, mesText, replyMarkup=None, parseMode='Markdown'):
    url = URL + 'editMessageText?chat_id={0}&message_id={1}&text={2}&parse_mode={3}'.format(chatId, mesId, mesText, parseMode)
    # get-запрос
    try:
        if replyMarkup:
            response = requests.get(url, data=replyMarkup)
        else:
            response = requests.get(url)
        response = response.json()
    # не удался
    except:
        print('Exception in editMessage method')
        return None
    # удался
    else:
        return response


#
# я дарю ему жизнь
if __name__ == '__main__':
    cb = CentralBankParser()
    helpList = CentralBankParser.getHelpList()
    while True:
        necessary = getNecessaryUpd()
        if necessary:
            for upd in necessary:
                #
                # нажатие кнопки
                if 'callback_query' in upd:
                    query = upd['callback_query']
                    mes = query['message']
                    helpMes = helpList[int(query['data'])]
                    editMessage(mes['chat']['id'], mes['message_id'], helpMes['text'], helpMes['markup'])
                #
                # текстовое сообщение
                else:
                    mes = upd['message']
                    mesObj = cb.parseMesText(mes['text'])
                    # если запарсилось, значит свежая таблица валют
                    if mesObj:
                        #
                        # вывод инструкции
                        if not mesObj['ok']:
                            helpMes = helpList[mesObj['page']]
                            sentMes = sendMessage(mes['chat']['id'], helpMes['text'], helpMes['markup'])
                            if sentMes and not sentMes['ok']:
                                print(sentMes)
                        else:
                            type = mesObj['type']
                            #
                            # вывод курса
                            if type == 'cost':
                                currency = cb.currencyTable[mesObj['cur']]
                                respMes = 'Цена на _{0} {1}_: *{2:.2f}*'
                                respMes = respMes.format(currency['nominal'], currency['name'], currency['value'])
                                sentMes = sendMessage(mes['chat']['id'], respMes)
                                if sentMes and not sentMes['ok']:
                                    print(sentMes)
                            #
                            # конвертер
                            elif type == 'convert':
                                # в рубли
                                if mesObj['to'] == 'RUB':
                                    currency = cb.currencyTable[mesObj['from']]
                                    value = (currency['value'] / currency['nominal']) * mesObj['amount']
                                # из рублей
                                elif mesObj['from'] == 'RUB':
                                    currency = cb.currencyTable[mesObj['to']]
                                    value = (currency['nominal'] / currency['value']) * mesObj['amount']
                                # кастомная конвертация
                                else:
                                    fromCur = cb.currencyTable[mesObj['from']]
                                    toCur = cb.currencyTable[mesObj['to']]
                                    value = ((fromCur['value'] / fromCur['nominal']) /
                                             (toCur['value'] / toCur['nominal'])) * mesObj['amount']
                                # оформление и отправка
                                respMes = 'Конвертер валют\n_{0} {1} -> {2}_: *{3:.2f}*'
                                respMes = respMes.format(mesObj['amount'], mesObj['from'], mesObj['to'], value)
                                sentMes = sendMessage(mes['chat']['id'], respMes)
                                if sentMes and not sentMes['ok']:
                                    print(sentMes)
                            #
                            # построение графика
                            elif type == 'graph':
                                image = cb.getImage(mesObj['cur'], mesObj['fromDate'])
                                if image:
                                    sentMes = sendPhoto(mes['chat']['id'], image)
                                else:
                                    respMes = '*Произошла ошибка* при построении _динамики котировок_'
                                    sentMes = sendMessage(mes['chat']['id'], respMes)
                                if sentMes and not sentMes['ok']:
                                    print(sentMes)
                            #
                            # вывод всех валют
                            elif type == 'all':
                                respMes = cb.getAllMes()
                                sentMes = sendMessage(mes['chat']['id'], respMes)
                                if sentMes and not sentMes['ok']:
                                    print(sentMes)
                            #
                            # первый запуск бота
                            elif type == 'start':
                                respMes = '*Здравствуйте!*\nЯ умею:'
                                sentMes = sendMessage(mes['chat']['id'], respMes)
                                if sentMes:
                                    if sentMes['ok']:
                                        helpMes = helpList[0]
                                        sentMes = sendMessage(mes['chat']['id'], helpMes['text'], helpMes['markup'])
                                        if sentMes and not sentMes['ok']:
                                            print(sentMes)
                                    else:
                                        print(sentMes)