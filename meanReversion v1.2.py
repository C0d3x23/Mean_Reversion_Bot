"""
Overview:

This bot is a Mean Reversion Strategy Trading Bot version 1.0.
Completion Date: June 23, 2023

Scans the daily and minute 5 SMA
Scans the minute 5 RSI
Trades single coin and 1 open position for the entire trading session only
Does not print specific details about the order
Does not store the data to a file for analysis purposes

Updates to be made:

store data to a file for analysis purposes
Fix the naming convention
schedule the trade
    Trade only during 2000H - 0800H
    Close open positions at closing session
Scan atleast 5 coins
Trade 2 open positions

Done:
Include a scan for open positions at the initial run
Print specific details for every order

Initial Balance = $61.29
"""
import ccxt
import pandas as pd
import credentials
import talib as ta
import numpy as np
import datetime
from pytz import timezone
import schedule
import time
import warnings

warnings.filterwarnings('ignore')

leverage = 5
marginMode = 'cross'
in_position = False

exchange = ccxt.binanceusdm({
    'enableRateLimit': True,
    'apiKey': credentials.api_key,
    'secret': credentials.api_secret,
    'defaultType': 'future'
})

def fetch_data(symbol, tf, limit):
    try:
        frame = pd.DataFrame(exchange.fetchOHLCV(symbol=symbol, timeframe=tf, limit=limit))
        frame = frame.iloc[:, :5]
        frame.columns = ['Timestamp', 'Open', 'High', 'Low', 'Close']
        frame['Timestamp'] = pd.to_datetime(frame.Timestamp, unit='ms')
        return frame
    except ccxt.RequestTimeout as e:
        print("Request Timeout. Retrying...")
        time.sleep(1)
        return fetch_data(symbol, tf, limit)

def SMA(df, window=200):
    df['SMA'] = df['Close'].rolling(window).mean()

def RSI(df, window=2):
    df['RSI'] = ta.RSI(np.array(df['Close']), window)

def update_data():
    global daily, m5

    # Fetch new data
    daily = fetch_data('SOL/USDT', '1d', 201)
    m5 = fetch_data('SOL/USDT', '5m', 201)

    # Calculate SMA
    SMA(daily)
    SMA(m5)

    # Calculate daily trend
    daily['daily_trend'] = daily['Close'] > daily['SMA']

    # Calculate m5 trend and overall trend
    m5['m5_trend'] = m5['Close'] > m5['SMA']
    m5['overall_trend'] = daily['daily_trend'] & m5['m5_trend']

    # Calculate RSI
    RSI(m5)

    m5['oversold'] = m5['RSI'] < 10
    m5['Buy'] = m5['overall_trend'] & m5.oversold
    m5['Sell'] = m5['RSI'] > 90
    m5['Buy'] = m5['Buy'].shift().fillna(False)
    m5['Sell'] = m5['Sell'].shift().fillna(False)

def buy_sell():
    global in_position

    if not in_position and m5.Buy.iloc[-1]:
        exchange.setLeverage(leverage=leverage, symbol='SOL/USDT')
        exchange.setMarginMode(marginMode=marginMode, symbol='SOL/USDT')
        ticker = exchange.fetchTicker('SOL/USDT')
        ask_price = float(ticker['info']['lastPrice'])
        balance = exchange.fetchBalance()['total']['USDT']
        buy_quantity = (balance * leverage) / ask_price
        buy = exchange.createMarketOrder('SOL/USDT', side='BUY', amount=buy_quantity)
        print(buy)
        symbol = buy['info']['symbol']
        side = buy['info']['side']
        unix = int(buy['info']['updateTime'])
        dt_object = datetime.datetime.fromtimestamp(unix / 1000)  # Divide by 1000 to convert from milliseconds to seconds
        timestamp = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        price = buy['price']
        amount = buy['amount']
        print(100 * '-')
        print(f'Timestamp     :    {timestamp} \n \
            Side          :    {side} \n \
            Symbol        :    {symbol} \n \
            Amount        :    {amount} \n \
            Price         :    $ {price}')
        print(100 * '-' + '\n')
        in_position = True

    else:
        if in_position:
            pos = exchange.fetchPositions(['SOL/USDT'])
            unrealizedPnl = pos[-1]['unrealizedPnl']
            percentage = pos[-1]['percentage']
            print(f' Stats : {unrealizedPnl} / {percentage}')

    if in_position and m5.Sell.iloc[-1]:
        pos = exchange.fetchPositions(symbols=['SOL/USDT'])
        sell_qty = float(pos[-1]['info']['positionAmt'])
        sell = exchange.createMarketOrder('SOL/USDT', side='SELL', amount=sell_qty)
        print(sell)
        symbol = sell['info']['symbol']
        side = sell['info']['side']
        unix = int(sell['info']['updateTime'])
        dt_object = datetime.datetime.fromtimestamp(unix / 1000)  # Divide by 1000 to convert from milliseconds to seconds
        timestamp = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        price = sell['price']
        amount = sell['amount']
        pnl((sell_price - buy_price) / buy_price) * 100
        print(100 * '-')
        print(f'Timestamp     :    {timestamp} \n \
            Side          :    {side} \n \
            Symbol        :    {symbol} \n \
            Amount        :    {amount} \n \
            Price         :    $ {price}')
        print(100 * '-' + '\n')
        in_position = False

    else:
        if not in_position and m5.overall_trend.iloc:
            print(".", end="", flush=True)

def scanPositions():
    global in_position

    pos = pd.DataFrame(exchange.fetchPositions(symbols=['SOL/USDT']))
    pos['Active'] = pos['entryPrice'] > 0
    active_count = (pos['Active'] == True).sum()
    open_positions = active_count == 1
    if open_positions:
        in_position = True
    else:
        pass

def MRB():
    scanPositions()
    update_data()
    buy_sell()

# Schedule the strategy to run every 10 seconds
schedule.every(10).seconds.do(MRB)

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except ccxt.RequestTimeout as e:
        print("Request Timeout. Retrying...")
        time.sleep(1)