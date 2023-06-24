import ccxt
import pandas as pd
import credentials
import numpy as np
import json
import schedule
import time

pd.set_option('display.max_rows', None)

import requests

API_KEY = '35e8a8c7-0d8a-4c85-87ec-bc61bf24df3f'  # Replace with your actual CoinMarketCap API key

top_crypto = []

def get_top_coins(limit=20):
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit={limit}'

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if response.status_code == 200:
        return data['data']
    else:
        print('Error occurred:', data['status']['error_message'])
        return []

# Usage example
top_coins = get_top_coins(20)
for coin in top_coins[:20]:  # Limit to top 10 coins
    rank = coin['cmc_rank']
    name = coin['name']
    symbol = coin['symbol'] + '/USDT'
    top_crypto.append(symbol)  # Append coin data as a dictionary

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
        if pair_volume > 250000 and coin in top_crypto:  # Add the condition to check if the coin is in top_crypto list
            combined_data.append({'Coin': coin, 'Correlation': correlation, 'Volume': pair_volume})

    combined_df = pd.DataFrame(combined_data)
    print(combined_df)
    
    # Save data to JSON file without backslashes
    with open('combined_data.json', 'w') as file:
        json.dump(combined_data, file)
    
    print('finished!')

# Schedule the job to run every hour
schedule.every(1).hour.do(job)

# Keep the script running indefinitely
while True:
    schedule.run_pending()
    time.sleep(1)
