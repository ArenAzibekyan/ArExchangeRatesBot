import requests


def cry_usd(currency):
    url = 'https://yobit.net/api/2/' + currency + '_usd/ticker'
    try:
        response = requests.get(url)
    except:
        return None
    else:
        data = response.json()['ticker']
        return (data['low'], data['high'], data['avg'])

