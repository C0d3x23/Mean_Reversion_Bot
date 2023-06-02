# import ccxt
# import pandas as pd
# import credentials
# import talib as ta
# import numpy as np
# import datetime
# from pytz import timezone
# import schedule
# import time

# exchange = ccxt.binanceusdm({
#     'enableRateLimit': True,
#     'apiKey': credentials.api_key,
#     'secret': credentials.api_secret,
#     'defaultType': 'future'
# })

# # Variables
# symbols = ['ETH/USDT','SOL/USDT', 'ADA/USDT','BNB/USDT','LTC/USDT','DOGE/USDT','MATIC/USDT','LINK/USDT']
# trend = '1d'
# execTf = '15m'
# rsiPeriod = 2
# rsiOverBought = 90
# rsiOverSold = 10
# smaPeriod = 200
# startTrade = 21  # New York session start time (9:00 PM UTC)
# endTrade = 11  # London session end time (11:00 AM UTC)
# leverage = 1
# marginMode = 'cross'

# inPosition = False

# def fetchOpenPositions(symbol):
#     positions = exchange.fetchPositions(symbols=[symbol])
#     for position in positions:
#         order = float(position['info']['unRealizedProfit'])
#         if order != 0.00000000:
#             print(f'{symbol} {order}')

# def fetchDailyTrend(symbol):
#     dailyBars = exchange.fetchOHLCV(symbol, timeframe=trend, limit=smaPeriod)
#     dailyClosePrice = [bar[4] for bar in dailyBars]
#     dailySma = ta.SMA(np.array(dailyClosePrice), smaPeriod)
#     if dailyClosePrice[-1] > dailySma[-1]:
#         print(f'{symbol} is bullish, waiting for exec_tf confirmation')
#         return True
#     return False

# def checkExecTfRsi(symbol):
#     execTfBars = exchange.fetchOHLCV(symbol, timeframe=execTf, limit=smaPeriod)
#     execTfClosePrice = [bar[4] for bar in execTfBars]
#     execTfRsi = ta.RSI(np.array(execTfClosePrice), rsiPeriod)
#     return execTfRsi[-1]

# def buyingCondition(symbol):
#     exchange.setLeverage(leverage = leverage, symbol=symbol)
#     exchange.setMarginMode(marginMode = marginMode, symbol=symbol)
#     ticker = exchange.fetchTicker((symbol))
#     askPrice = ticker['close']
#     balance = exchange.fetchBalance()['total']['USDT']
#     buyQuantity = (balance * 0.5) / askPrice
#     buy = exchange.createMarketOrder(symbol, side='BUY', amount=buyQuantity)
#     print(buy)
#     print('------------------------------------')

# def sellingCondition(symbol):
#     ticker = exchange.fetchTicker((symbol))
#     bidPrice = ticker['close']
#     coinBalance = exchange.fetchBalance()['total'][symbol.split('/')[0]]
#     sellQuantity = coinBalance / bidPrice
#     sell = exchange.createMarketOrder(symbol, side='SELL', amount=sellQuantity)
#     print(sell)

# def MeanReversionBot():
#     global inPosition
#     execTfRsi = None  # Initialize execTfRsi variable

#     for symbol in symbols:
#         if execTfRsi < rsiOverSold:
#             fetchDailyTrend(symbol)
#             execTfRsi = checkExecTfRsi(symbol)
#             buyingCondition(symbol)
#             fetchOpenPositions(symbol)
#             inPosition = True
#             break

#     if inPosition:
#         fetchDailyTrend(symbol)
#         execTfRsi = checkExecTfRsi(symbol)
#         if execTfRsi > rsiOverBought:
#             sellingCondition(symbol)
#             inPosition = False

# def runBot():
#     MeanReversionBot()

# schedule.every(10).seconds.do(runBot)

# while True:
#     schedule.run_pending()
#     time.sleep(1)



# # def MeanReversionBot():
# #     global inPosition

# #     for symbol in symbols:
# #         if fetchOpenPositions(symbol):
# #             inPosition = True
# #             break

# #     if inPosition:
# #         return

# #     for symbol in symbols:
# #         if fetchOpenPositions(symbol):
# #             execTfRsi = checkExecTfRsi(symbol)
# #             if execTfRsi > rsiOverBought and inPosition:
# #                 sellingCondition(symbol)
# #                 inPosition = False
# #                 break
# #             elif execTfRsi < rsiOversold and not inPosition:
# #                 fetchDailyTrend(symbol)
# #                 buyingCondition(symbol)
# #                 fetchOpenPositions(symbol)
# #                 break


# # def runBot():
# #     MeanReversionBot()


# # schedule.every(10).seconds.do(runBot)

# # while True:
# #     schedule.run_pending()
# #     time.sleep(1)



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

def fetch_open_positions():
    for symbol in symbols:
        positions = exchange.fetchPositions(symbols=[symbol])
        for position in positions:
            order = float(position['info']['unRealizedProfit'])
            if order != 0.00000000:
                print(f'{symbol} {order}')
