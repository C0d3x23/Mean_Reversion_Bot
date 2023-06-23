import ccxt
import pandas as pd
import datetime
import time


def fetch_data(symbol, timeframe, limit):
    exchange = ccxt.binance()

    exchange.load_markets()
    symbol_info = exchange.market(symbol)
    exchange_symbol = symbol_info['symbol']
    exchange_timeframe = symbol_info['timeframes'][timeframe]

    data = exchange.fetch_ohlcv(exchange_symbol, timeframe=exchange_timeframe, limit=limit)
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    return df


def should_buy(symbol, timeframe):
    df = fetch_data(symbol, timeframe, limit=201)

    df['200sma'] = df['close'].rolling(window=200).mean()
    df['rsi'] = calculate_rsi(df['close'], period=14)

    if df['200sma'].iloc[-1] > df['close'].iloc[-1] and \
       df['200sma'].iloc[-2] > df['close'].iloc[-2] and \
       df['rsi'].iloc[-1] < 30:
        return True
    else:
        return False


def place_trade(symbol, quantity, side):
    exchange = ccxt.binance()

    order = exchange.create_market_order(symbol=symbol, type='market', side=side, amount=quantity)
    
    try:
        result = exchange.create_order(order)
        return result['id']
    except Exception as e:
        print(f"Trade failed: {str(e)}")
        return None


def check_pnl():
    exchange = ccxt.binance()

    open_positions = exchange.fetch_open_orders()

    for position in open_positions:
        symbol = position['symbol']
        trade_id = position['id']
        side = position['side']
        quantity = position['amount']

        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']

        pnl = (current_price - position['price']) * quantity

        print(f"Trade ID: {trade_id} | Symbol: {symbol} | Side: {side} | PNL: {pnl}")


def calculate_rsi(data, period):
    # Implement your RSI calculation logic here
    pass


# Example usage:
if __name__ == "__main__":
    symbol = 'BTC/USDT'
    timeframe = '5m'
    quantity = 0.1
    side = 'buy'

    while True:
        if should_buy(symbol, timeframe):
            trade_id = place_trade(symbol, quantity, side)
            if trade_id:
                print(f"Trade placed. ID: {trade_id}")

        check_pnl()
        time.sleep(60)  # Adjust the sleep duration according to your needs

"""

print(100 * '-')
print(f'Side          :    {side}')
print(f'Timestamp     :    {buy_time} \nSymbol        :    {buy_symbol} \nAmount        :    {buy_amount}')
print(f'Price         :    $ {buy_price}')
print(100 * '-' + '\n')

----------------------------------------------------------------------------------------------------
Side          :    sell
Timestamp     :    2023-06-17 03:03:59 
Symbol        :    ETHUSDT 
Amount        :    1.000
Price         :    $ 1720.0
----------------------------------------------------------------------------------------------------

"""