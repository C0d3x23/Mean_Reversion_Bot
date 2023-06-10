""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Mean Reversion Bot

Import necessary Libraries
Import API Connection and credentials
Import variables 
Check volume per coin, 100k above is the target coin to trade ### Done
Check the correlation of the altcoins to etherium, acceptable correlation will be traded and store it to a database ### Done
Use the filtered database  to refilter using the trading strategy indicators

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import ccxt
import pandas as pd
import credentials
import talib as ta
import numpy as np
import datetime
from pytz import timezone
import schedule
import time
from sqlalchemy import create_engine

sma_limit = 200

engine = create_engine('sqlite:///coin_correl_vol.db')

db = pd.read_sql('combined_data', engine)
# print(db)

exchange = ccxt.binanceusdm({
    'enableRateLimit': True,
    'apiKey': credentials.api_key,
    'secret': credentials.api_secret,
    'defaultType': 'future'
})

for _, row in db.iterrows():
    coin = row['Coin']
    daily_bars = exchange.fetchOHLCV(coin, timeframe = '1d', limit = sma_limit)
    daily_close = [bar[4] for bar in daily_bars]
    daily_sma = ta.SMA(np.array(daily_close), 200)

    if daily_close[-1] > daily_sma[-1]:
        exec_tf_bars = exchange.fetchOHLCV(coin, timeframe='5m', limit=sma_limit)
        exec_tf_close = [bar[4] for bar in exec_tf_bars]
        exec_tf_SMA = ta.SMA(np.array(exec_tf_close), sma_limit)

    if exec_tf_close[-1] > exec_tf_SMA[-1]:
        exec_tf_bar = exec_tf_bars
        exec_tf_close_price = [bar[4] for bar in exec_tf_bar]
        exec_tf_rsi = ta.RSI(np.array(exec_tf_close), rsi_period)
        print(f'{coin} is bullish, | RSI {exec_tf_rsi[-1]}')

    else:
        print('No bullish pairs at the moment')

