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

sma_limit = 200
rsi_period = 2
rsi_overbought = 90
rsi_oversold = 10
leverage = 5
marginMode = 'cross'
in_position = False

exchange = ccxt.binanceusdm({
        'enableRateLimit': True,
        'apiKey': credentials.api_key,
        'secret': credentials.api_secret,
        'defaultType': 'future'
})

def buy_sell_signal():
    """
    Executes buy and sell signals based on specific conditions.

    This function checks the buy and sell conditions for a trading strategy using the Relative Strength Index (RSI)
    and Simple Moving Average (SMA) indicators. It retrieves the necessary data, calculates indicators, and executes
    market orders based on the conditions. It also manages position status and prints relevant information.

    Parameters:
        None

    Returns:
        None
    """
    # calculatePositions()
    ohlcv()

    global in_position

    if not in_position and df['buy_trigger'].iloc[-1] < rsi_oversold:
        exchange.setLeverage(leverage=leverage, symbol='ETH/USDT')
        exchange.setMarginMode(marginMode=marginMode, symbol='ETH/USDT')
        ticker = exchange.fetchTicker('ETH/USDT')
        ask_price = float(ticker['info']['lastPrice'])
        balance = exchange.fetchBalance()['total']['USDT']
        buy_quantity = (balance * 0.25 * leverage) / ask_price
        buy = exchange.createMarketOrder('ETH/USDT', side='BUY', amount=buy_quantity)
        print(buy)
        print(2 * '\n' + 100 * '-')
        print(f'Buy executed for ETH/USDT at SMA: {daily_sma[-1]}, RSI: {exec_tf_rsi[-1]}')
        print(100 * '-' + '\n')
        in_position = True
    else:
        posi = exchange.fetchPositions(symbols=['ETH/USDT'])
        pnl = posi[-1]['percentage']
        print(f'Already in position, PnL = {pnl}')

    ######### The in_position varibale is not updating causing the code to not print the open positions
    if in_position and df['sell_confirmation'].iloc[-1] > rsi_overbought:
        # pos = exchange.fetchPositions(symbols = 'ETH/USDT')
        sell_qty = float(pos[-1]['info']['positionAmt'])
        sell = exchange.createMarketOrder('ETH/USDT', side='SELL', amount=sell_qty)
        print(sell)
        print(2 * '\n' + 100 * '-')
        print(f'Sell executed for ETH/USDT at SMA: {daily_sma[-1]}, RSI: {exec_tf_rsi[-1]}')
        print(100 * '-' + '\n')
        in_position = False

# def calculatePositions():
#     global in_position

#     pos = pd.DataFrame(exchange.fetchPositions(symbols=['ETH/USDT']))
#     pos['Active'] = pos['entryPrice'] > 0
#     active_count = (pos['Active'] == True).sum()
#     open_positions = active_count == 1
#     if open_positions:
#         in_position = True
#         p = pos[-1]['percentage']
#         print(f'Already in position, PnL = {p}')

#     time.sleep(5)

def daily(symbol, tf, limit):
    """
    Retrieves and processes daily OHLCV data for a given symbol.

    This function fetches the daily OHLCV (Open, High, Low, Close, Volume) data for a specified symbol from the exchange.
    It then calculates the daily Simple Moving Average (SMA) and determines the daily trend.

    Parameters:
        symbol (str): The symbol to fetch data for.
        tf (str): The timeframe for the OHLCV data.
        limit (int): The number of data points to retrieve.

    Returns:
        pd.DataFrame: A DataFrame containing the processed daily OHLCV data with SMA and trend columns.
    """
    # Daily SMA
    daily = pd.DataFrame(exchange.fetchOHLCV(symbol=symbol, timeframe=tf, limit=limit))
    daily = daily.iloc[:, :5]
    daily.columns = ['Timestamp', 'Open', 'High', 'Low', 'Close']
    daily['Timestamp'] = pd.to_datetime(daily['Timestamp'], unit='ms')
    daily['daily_sma'] = ta.SMA(np.array(daily['Close']), 200)
    daily['daily_trend'] = daily['Close'] > daily['daily_sma']
    return daily

def m5(symbol, timeframe, limit, rsi_period=2, rsi_overbought=90, rsi_oversold=10):
    """
    Retrieves and processes 5-minute OHLCV data for a given symbol.

    This function fetches the 5-minute OHLCV data for a specified symbol from the exchange.
    It calculates the 5-minute Simple Moving Average (SMA), determines the trend, and applies RSI (Relative Strength Index)
    indicators for buy and sell confirmations.

    Parameters:
        symbol (str): The symbol to fetch data for.
        timeframe (str): The timeframe for the OHLCV data.
        limit (int): The number of data points to retrieve.
        rsi_period (int): The period for calculating RSI.
        rsi_overbought (int): The RSI value above which the asset is considered overbought.
        rsi_oversold (int): The RSI value below which the asset is considered oversold.

    Returns:
        pd.DataFrame: A DataFrame containing the processed 5-minute OHLCV data with SMA, trend, and confirmation columns.
    """
    daily_df = daily('ETH/USDT', '1d', 200)
    # m5 SMA
    df = pd.DataFrame(exchange.fetchOHLCV(symbol=symbol, timeframe=timeframe, limit=limit))
    df = df.iloc[:, :5]
    df.columns = ['Timestamp', 'Open', 'High', 'Low', 'Close']
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df['m5_sma'] = ta.SMA(np.array(df['Close']), limit)
    df['m5_trend'] = df['Close'] > df['m5_sma']
    df['sma_trigger'] = daily_df['daily_trend'] & df['m5_trend']

    # m5 RSI
    df['m5_rsi'] = ta.RSI(np.array(df['Close']), rsi_period)
    df['m5_oversold'] = df['m5_rsi'] > rsi_oversold
    df['buy_confirmation'] = df['sma_trigger'] & df['m5_oversold']
    df['sell_confirmation'] = df['m5_rsi'] > rsi_overbought
    df['buy_trigger'] = df['buy_confirmation'].shift(-1).fillna(False)
    return df

    if df['buy_confirmation'].iloc[-1]:
        print(".", end="", flush=True)


schedule.every(10).seconds.do(ohlcv)

while True:
    schedule.run_pending()
    time.sleep(1)
