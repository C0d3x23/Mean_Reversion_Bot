import ccxt
import pandas as pd
import credentials
import talib as ta
import numpy as np
import datetime
from pytz import timezone
import schedule
import time

exchange = ccxt.binance({
    'enableRateLimit': True,
    'apiKey': credentials.api_key,
    'secret': credentials.api_secret,
})

# Variables
symbols = ['SOL/USDT', 'ADA/USDT','BNB/USDT','LTC/USDT']  # Updated variable name from symbolS to symbols
trend = '1D'
exec_tf = '15m'
rsi_period = 2
rsi_overbought = 90
rsi_oversold = 10
sma_period = 200
max_open_position = 3
per_trade_amount = 1.0
per_trade_sell = 1.0
start_trade = 21  # New York session start time (9:00 PM UTC)
end_trade = 11  # London session end time (11:00 AM UTC)

in_position = False

def MeanReversionBot():
    global in_position

    # # Get the current UTC time
    # utc_now = datetime.datetime.now(timezone('UTC'))

    # # Convert UTC time to Philippines time
    # ph_timezone = timezone('Asia/Manila')
    # ph_time = utc_now.astimezone(ph_timezone).time()

    # # Check if it's within the trading window
    # if start_trade <= ph_time.hour <= end_trade:
    print('Scanning')
    for symbol in symbols:
        # Fetch OHLCV data
        daily_bars = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=sma_period)
        daily_close_price = [bar[4] for bar in daily_bars]
        daily_sma = ta.SMA(np.array(daily_close_price), sma_period)

        # Check daily trend
        if daily_close_price[-1] > daily_sma[-1]:
            print(f'{symbol} is bullish, waiting for m15_rsi confirmation')
            m15_bars = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=sma_period)
            m15_close_price = [bar[4] for bar in m15_bars]
            m15_rsi = ta.RSI(np.array(m15_close_price), rsi_period)

            if m15_rsi[-1] < rsi_oversold:
                if not in_position:
                    balance = exchange.fetch_balance()['total']['USDT']
                    trade_amount = balance * per_trade_amount
                    buy = exchange.create_market_buy_order(symbol, trade_amount)
                    print(buy)
                    in_position = True
                else:
                    print("Already in a position")

            elif m15_rsi[-1] > rsi_overbought:
                if in_position:
                    coin_balance = exchange.fetch_balance()['total'][symbol.split('/')[0]]
                    sell_amount = coin_balance * per_trade_sell
                    sell = exchange.create_market_sell_order(symbol, sell_amount)
                    print(sell)
                    in_position = False
                else:
                    print('No open positions yet')

def run_bot():
    MeanReversionBot()

schedule.every(10).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
