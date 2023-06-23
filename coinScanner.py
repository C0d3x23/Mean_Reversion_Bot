import ccxt
import pandas as pd
import credentials
import numpy as np
from sqlalchemy import create_engine
import schedule
import time

engine = create_engine('sqlite:///coin_correl_vol.db')

def job():
    exchange = ccxt.binanceusdm({
        'enableRateLimit': True,
        'apiKey': credentials.api_key,
        'secret': credentials.api_secret,
        'defaultType': 'future'
    })

    info = exchange.fetchPositions()
    symbols = [market['symbol'] for market in info]
    relevant = [symbol.split('USDT')[0] + 'USDT' for symbol in symbols if symbol.endswith('USDT')]

    def get_daily_data(symbol):
        frame = pd.DataFrame(exchange.fetchOHLCV(symbol, timeframe='1d', limit=20))
        if len(frame) > 0:
            frame = frame.iloc[:, :6]
            frame.columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            frame = frame.set_index('Timestamp')
            frame.index = pd.to_datetime(frame.index, unit='ms')
            frame = frame.astype(float)
            return frame

    dfs = []

    for coin in relevant:
        dfs.append(get_daily_data(coin))

    merged_df = pd.concat(dict(zip(relevant, dfs)), axis=1)
    close_df = merged_df.loc[:, merged_df.columns.get_level_values(1).isin(['Close'])]
    close_df.columns = close_df.columns.droplevel(1)
    log_returns_df = np.log(close_df.pct_change() + 1)
    coin_correl = log_returns_df.corr()
    filtered_coins = coin_correl['ETH/USDT'][coin_correl['ETH/USDT'] >= 0.75]
    filtered_coins = filtered_coins.sort_values(ascending=False)

    combined_data = []

    for coin, correlation in filtered_coins.items():
        pair_volume = merged_df[coin]['Volume'].iloc[-1]  # Get the volume of the pair
        if pair_volume > 250000:
            combined_data.append({'Coin': coin, 'Correlation': correlation, 'Volume': pair_volume})

    combined_df = pd.DataFrame(combined_data)
    print(combined_df)
    combined_df.to_sql('combined_data', engine, if_exists='replace', index=False)
    print('finised!')

# Schedule the job to run every hour
schedule.every(5).seconds.do(job)

# Keep the script running indefinitely
while True:
    schedule.run_pending()
    time.sleep(1)
