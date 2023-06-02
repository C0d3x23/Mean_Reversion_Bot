import ccxt
import credentials

exchange = ccxt.binanceusdm({
    'enableRateLimit': True,
    'apiKey': credentials.api_key,
    'secret': credentials.api_secret
})

# help = exchange.has
# print(help)
symbol = ['BTC/USDT', 'ETH/USDT']
leverage = 10

for sym in symbol:
    positions = exchange.fetchPositions(symbols=[sym])
    for position in positions:
        order = float(position['info']['positionAmt'])
        print(order)
        if order > 1:
            print('1')
        else:
            print('0')
    # print(new_order)