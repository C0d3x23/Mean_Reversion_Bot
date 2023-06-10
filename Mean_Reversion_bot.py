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
trend = '1d'
exec_tf = '5m'
rsi_period = 2
rsi_overbought = 90
rsi_oversold = 10
sma_period = 200
start_trade = 21  # New York session start time (9:00 PM UTC)
end_trade = 11  # London session end time (11:00 AM UTC)
leverage = 1
marginMode = 'cross'
in_position = False

# def fetch_open_positions():
#     in_position = False
#     positions = exchange.fetchPositions(symbols = ['ETH/USDT'])[-1]['info']['unRealizedProfit']
#     if positions != 0.00000000:
#         print(f' ETH/USDT {positions}')
#         in_position = True
#         return in_position
#     return in_position

def MeanReversionBot():
    global in_position

    pos = float(exchange.fetchPositions(symbols=['ETH/USDT'])[-1]['info']['entryPrice'])
    if pos > 0:
        in_position = True

    daily_bars = exchange.fetchOHLCV('ETH/USDT', timeframe=trend, limit=sma_period)
    daily_close_price = [bar[4] for bar in daily_bars]
    daily_sma = ta.SMA(np.array(daily_close_price), sma_period)

    if daily_close_price[-1] > daily_sma[-1]:
        exec_tf_bars = exchange.fetchOHLCV('ETH/USDT', timeframe=exec_tf, limit=sma_period)
        exec_tf_close_price = [bar[4] for bar in exec_tf_bars]
        exec_tf_rsi = ta.RSI(np.array(exec_tf_close_price), rsi_period)
        print(f'ETH/USDT is bullish, | RSI {exec_tf_rsi[-1]}')

    if not in_position:
        if exec_tf_rsi[-1] < rsi_oversold:
            exchange.setLeverage(leverage = leverage, symbol='ETH/USDT')
            exchange.setMarginMode(marginMode = marginMode, symbol='ETH/USDT')
            ticker = exchange.fetchTicker('ETH/USDT')
            ask_price = ticker['close']
            balance = exchange.fetchBalance()['total']['USDT']
            buy_quantity = balance / ask_price
            buy = exchange.createMarketOrder('ETH/USDT', side = 'BUY', amount = buy_quantity)
            print(buy)
            print(2 * '\n' + 100* '-')
            print(f'Buy executed for ETH/USDT at SMA: {daily_sma[-1]}, RSI: {exec_tf_rsi[-1]}')
            print(100 * '-' + '\n')
            in_position = True
        
    else:
        pnl = exchange.fetchPositions(symbols=['ETH/USDT'])[-1]['unrealizedPnl']
        print(f'Already in position, PnL = {pnl}')

    if in_position:
        if exec_tf_rsi[-1] > rsi_overbought:
            sell_qty = exchange.fetchMyTrades('ETH/USDT')[-1]['info']['qty']
            sell = exchange.createMarketOrder('ETH/USDT', side = 'SELL', amount = sell_qty)
            print(sell)
            print(2 * '\n' + 100* '-')
            print(f'Sell executed for ETH/USDT at SMA: {daily_sma[-1]}, RSI: {exec_tf_rsi[-1]}')
            print(100 * '-' + '\n')
            in_position = False
    
    else:
        print('Scanning for Trades')

def run_bot():
    MeanReversionBot()

schedule.every(10).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
