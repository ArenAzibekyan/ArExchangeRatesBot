import requests


def cry_usd(currency):
    url = 'https://yobit.net/api/2/' + currency + '_usd/ticker'
    try:
        response = requests.get(url)
        data = response.json()['ticker']
    except:
        return None
    else:
        return (data['low'], data['high'], data['avg'])