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
exec_tf = '15m'
rsi_period = 2
rsi_overbought = 90
rsi_oversold = 10
sma_period = 200
start_trade = 21  # New York session start time (9:00 PM UTC)
end_trade = 11  # London session end time (11:00 AM UTC)
leverage = 1
marginMode = 'cross'

def MeanReversionBot(in_position = False):

    print('Fetching data...')
    entry_prices = {}  # Dictionary to store entry prices

    for symbol in symbols:
        positions = exchange.fetchPositions(symbols=[symbol])
        for position in positions:
            order = float(position['info']['positionAmt'])
            if order > 1:
                print ('Already in position')
                print(f'{symbol} {order}')
                in_position = True
                break

        if in_position:
            break

        # Fetch OHLCV data
        daily_bars = exchange.fetchOHLCV(symbol, timeframe=trend, limit=sma_period)
        daily_close_price = [bar[4] for bar in daily_bars]
        daily_sma = ta.SMA(np.array(daily_close_price), sma_period)

        # Check daily trend
        if daily_close_price[-1] > daily_sma[-1]:
            print(f'{symbol} is bullish, waiting for m15_rsi confirmation')
            exec_tf_bars = exchange.fetchOHLCV(symbol, timeframe=exec_tf, limit=sma_period)
            exec_tf_close_price = [bar[4] for bar in exec_tf_bars]
            exec_tf_rsi = ta.RSI(np.array(exec_tf_close_price), rsi_period)

            if exec_tf_rsi[-1] < rsi_oversold and not in_position:
                exchange.setLeverage(leverage = leverage, symbol=symbol)
                exchange.setMarginMode(marginMode = marginMode, symbol=symbol)
                ticker = exchange.fetchTicker((symbol))
                ask_price = ticker['close']
                balance = exchange.fetchBalance()['total']['USDT']
                buy_quantity = (balance * 0.5) / ask_price
                buy = exchange.createMarketOrder(symbol, side = 'BUY', amount = buy_quantity)  # Specify market type as futures
                print(buy)
                in_position = True
                print('------------------------------------------------------------------------------')
                positions = exchange.fetchPositions(symbols=[symbol])
                for position in positions:
                    order = float(position['info']['positionAmt'])
                    if order > 1:
                        print ('Already in position')
                        print(f'{symbol} {order}')
                        in_position = True
                        break

        if exec_tf_rsi[-1] > rsi_overbought and in_position:
            bid_price = ticker['close']
            coin_balance = exchange.fetchBalance()['total'][symbol.split('/')[0]]
            sell_quantity = coin_balance / bid_price
            sell = exchange.createMarketOrder(symbol, side = 'SELL', amount = sell_quantity)
            print(sell)
            in_position = False
            print('No open positions yet')
            break

def run_bot():
    MeanReversionBot()

schedule.every(10).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
