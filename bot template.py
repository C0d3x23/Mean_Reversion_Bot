# Constants
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
TIMEFRAME = '15m'
DAILY_TIMEFRAME = '1d'  # Daily timeframe
SMA_PERIOD = 200
RSI_PERIOD = 2
RSI_OVERBOUGHT = 80
RSI_OVERSOLD = 28
TRADE_WINDOW_START = 8
TRADE_WINDOW_END = 20
MAX_POSITIONS = 3
TRADE_AMOUNT_PERCENTAGE = 0.1  # 10% of account balance per trade

async def main():
    # Create Binance exchange instance
    exchange = ccxt.binance({
        'apiKey': 'UMjRag1HfZFAaL5FgU4sfBS5R4WUOXLKPVOspmjZgsNyxk2Tk16iIumbtH2oVhub',
        'secret': 'tGhc7g0FyHZyOOwmmP9q0DCOy8dQA9MXZJYiGS5mRQPQ5awJs8BMkVuHjuRvLHyU',
    })
    
    # Start trading loop
    while True:
        # Check if it's within the trading window
        current_hour = datetime.datetime.now().hour
        if current_hour >= TRADE_WINDOW_START and current_hour < TRADE_WINDOW_END:
            # Iterate over symbols
            for symbol in SYMBOLS:
                # Fetch daily data
                daily_bars = await exchange.fetch_ohlcv(symbol, timeframe=DAILY_TIMEFRAME, limit=SMA_PERIOD)
                daily_close_prices = [bar[4] for bar in daily_bars]  # Daily closing prices
                
                # Calculate daily SMA
                daily_sma = talib.SMA(np.array(daily_close_prices), SMA_PERIOD)
                
                # Check daily trend
                if daily_close_prices[-1] > daily_sma[-1]:
                    # Fetch 15-minute data
                    bars = await exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=SMA_PERIOD)
                    close_prices = [bar[4] for bar in bars]  # Closing prices
                    
                    # Calculate SMA
                    sma = talib.SMA(np.array(close_prices), SMA_PERIOD)
                    
                    # Fetch current RSI value
                    last_bar = await exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=1)
                    current_price = last_bar[0][4]  # Current closing price
                    rsi = talib.RSI(np.array(close_prices), RSI_PERIOD)
                    current_rsi = rsi[-1]
                    
                    # Check trading conditions
                    if current_price > sma[-1] and current_rsi < RSI_OVERSOLD:
                        # Check open position limit
                        open_positions = len(exchange.fetch_open_orders(symbol))
                        if open_positions < MAX_POSITIONS:
                            # Get account balance
                            balance = exchange.fetch_balance()['total']['USDT']
                            # Calculate trade amount
                            trade_amount = balance * TRADE_AMOUNT_PERCENTAGE
                            price = current_price  # Current market price
                            await exchange.create_market_buy_order(symbol, trade_amount)
                            print(f"Entered trade: {symbol}")
                    
                    # Check for exit condition
                    if current_rsi > RSI_OVERBOUGHT:
                        open_positions = len(exchange.fetch_open_orders(symbol))
                        if open_positions > 0:
                            # Exit trade
                            open_orders = exchange.fetch_open_orders(symbol)
                            for order in open_orders:
                                await exchange.cancel_order(order['id'])
                                print(f"Exited trade: {symbol}")
        
        # Sleep for 1 minute before next iteration
        await asyncio.sleep(60)

# Run the trading bot
asyncio.run(main())
