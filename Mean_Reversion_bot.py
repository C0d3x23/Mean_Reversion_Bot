import ccxt
import pandas as pd
import credentials
import talib as ta
import numpy as np
import datetime

exchange = ccxt.binance({
    'enableRateLimit': True,
    'apiKey': credentials.api_key,
    'secret': credentials.api_secret,
})

#Variables

symbols = ['BTC/USDT','ETH/USDT','ADA/USDT','SOL/USDT']
trend = '1D'
exec_tf = '15m'
rsi_period = 2
rsi_overbought = 80
rsi_oversold = 28
sma_period = 200
max_open_position = 3
per_trade_amount = 0.1
start_trade = 15
end_trade = 3

while True:
    # Check if it's within the trading window
    current_hour = datetime.datetime.now().hour
    if current_hour >= start_trade and current_hour <= end_trade:
 
        for symbol in symbols:
            # Fetch OHLCV data
            daily_bars = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=sma_period)
            daily_close_price = [bar[4] for bar in daily_bars]
            daily_sma = ta.SMA(np.array(daily_close_price), sma_period)
            print(f'Daily SMA = {symbol} | {daily_sma[-1]}')

            #Check daily trend
            if daily_close_price[-1] > daily_sma[-1]:
                m15_bars = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=sma_period)
                m15_close_price = [bar[4] for bar in m15_bars]
                m15_sma = ta.SMA(np.array(m15_close_price),sma_period)

                if m15_close_price > m15_sma:
                    m15_rsi = ta.RSI(np.array(m15_close_price), rsi_period)
                    print(f'm15_RSI = {symbol} | {m15_rsi[-1]}')
                    last_bar = m15_bars

                    if m15_rsi[-1] < rsi_oversold:
                        open_positions = sum(len(exchange.fetch_open_orders(symbol)) for symbol in symbols)
                        if open_positions < max_open_position:
                            balance = exchange.fetch_balance()['total']['USDT']
                            trade_amount = balance * per_trade_amount
                            buy = exchange.create_market_buy_order(symbol, trade_amount)
                            print(f'Entered Trade: {symbol}')

                    elif m15_rsi[-1] > rsi_overbought:
                        open_positions = sum(len(exchange.fetch_open_orders(symbol)) for symbol in symbols)
                        if open_positions > 0:
                            open_orders = exchange.fetch_open_orders(symbol)
                            for order in open_orders:
                                sell = exchange.cancel_order(order['id'])
                                print(f'Exited Trade: {symbol}')

    else:
        break