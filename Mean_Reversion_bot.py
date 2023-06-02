import ccxt
import pandas as pd
import credentials
import talib as ta
import numpy as np
import datetime
from pytz import timezone
import schedule
import time

exchange = ccxt.binanceusdm({
    'enableRateLimit': True,
    'apiKey': credentials.api_key,
    'secret': credentials.api_secret,
    'defaultType': 'future'
})

# Variables
symbols = ['ETH/USDT','SOL/USDT', 'ADA/USDT','BNB/USDT','LTC/USDT','DOGE/USDT','MATIC/USDT','LINK/USDT']
trend = '1d'
exec_tf = '1m'
rsi_period = 2
rsi_overbought = 90
rsi_oversold = 10
sma_period = 200
start_trade = 21  # New York session start time (9:00 PM UTC)
end_trade = 11  # London session end time (11:00 AM UTC)
leverage = 1
marginMode = 'cross'
in_position = False
initialized = False  # Flag to track if the code has been initialized

def fetch_open_positions():
    in_position = False
    for symbol in symbols:
        positions = exchange.fetchPositions(symbols=[symbol])
        for position in positions:
            order = float(position['info']['unRealizedProfit'])
            if order != 0.00000000:
                print(f'{symbol} {order}')
                in_position = True
                break
    return in_position

def MeanReversionBot():
    global in_position
    global initialized

    if not initialized:
        print('Initializing Bot...')
        initialized = True

    for symbol in symbols:
        in_position = fetch_open_positions()
        exec_tf_rsi = None  # Default value

        if not in_position:

                # Fetch OHLCV data
                daily_bars = exchange.fetchOHLCV(symbol, timeframe=trend, limit=sma_period)
                daily_close_price = [bar[4] for bar in daily_bars]
                daily_sma = ta.SMA(np.array(daily_close_price), sma_period)

                # Check daily trend
                if daily_close_price[-1] > daily_sma[-1]:
                    print(f'{symbol} is bullish, waiting for exec_tf confirmation')
                    exec_tf_bars = exchange.fetchOHLCV(symbol, timeframe=exec_tf, limit=sma_period)
                    exec_tf_close_price = [bar[4] for bar in exec_tf_bars]
                    exec_tf_rsi = ta.RSI(np.array(exec_tf_close_price), rsi_period)

                    if exec_tf_rsi[-1] < rsi_oversold:
                        exchange.setLeverage(leverage = leverage, symbol=symbol)
                        exchange.setMarginMode(marginMode = marginMode, symbol=symbol)
                        ticker = exchange.fetchTicker((symbol))
                        ask_price = ticker['close']
                        balance = exchange.fetchBalance()['total']['USDT']
                        buy_quantity = (balance * 0.5) / ask_price
                        buy = exchange.createMarketOrder(symbol, side = 'BUY', amount = buy_quantity)
                        print(buy)
                        in_position = fetch_open_positions()

        if in_position:
            if  exec_tf_rsi is not None and exec_tf_rsi[-1] > rsi_overbought:
                bid_price = ticker['close']
                coin_balance = exchange.fetchBalance()['total'][symbol.split('/')[0]]
                sell_quantity = coin_balance / bid_price
                sell = exchange.createMarketOrder(symbol, side = 'SELL', amount = sell_quantity)
                print(sell)
                in_position = False
                print('No open positions yet')

def run_bot():
    MeanReversionBot()

schedule.every(10).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
