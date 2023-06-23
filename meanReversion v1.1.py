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

Print specific details for every order
store data to a file for analysis purposes
Fix the naming convention
schedule the trade
    Trade only during 2000H - 0800H
    Close open positions at closing session
    Include a scan for open positions at the initial run

Trade atleast 5 coins
Trade 2 open positions

Initial Balance = $46.89
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
    daily = fetch_data('ETH/USDT', '1d', 201)
    m5 = fetch_data('ETH/USDT', '5m', 201)

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
    print(".", end="", flush=True)

def buy_sell():
    global in_position

    if not in_position and m5.Buy.iloc[-1]:
        exchange.setLeverage(leverage=leverage, symbol='ETH/USDT')
        exchange.setMarginMode(marginMode=marginMode, symbol='ETH/USDT')
        ticker = exchange.fetchTicker('ETH/USDT')
        ask_price = float(ticker['info']['lastPrice'])
        balance = exchange.fetchBalance()['total']['USDT']
        buy_quantity = (balance * leverage) / ask_price
        buy = exchange.createMarketOrder('ETH/USDT', side='BUY', amount=buy_quantity)
        print(buy)
        in_position = True

    if in_position and m5.Sell.iloc[-1]:
        pos = exchange.fetchPositions(symbols=['ETH/USDT'])
        sell_qty = float(pos[-1]['info']['positionAmt'])
        sell = exchange.createMarketOrder('ETH/USDT', side='SELL', amount=sell_qty)
        print(sell)
        in_position = False

def scanPositions():
    global in_position

    pos = pd.DataFrame(exchange.fetchPositions(symbols=['ETH/USDT']))
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