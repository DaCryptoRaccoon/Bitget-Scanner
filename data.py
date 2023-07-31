import time
import requests
from tabulate import tabulate
from colorama import init, Fore
from plyer import notification
import os
import random
from datetime import datetime, timedelta
import csv

# Constants
REST_API_URL = 'https://api.bitget.com'
DEPTH_LEVEL = 20
LIQUIDITY_WINDOW_SIZE = 10  # Number of data points for calculating average liquidity
LIQUIDITY_THRESHOLD = 0.5   # 20% deviation from average liquidity to trigger alert

# Colorama initialization for colored text
init()

def read_historical_data(pair):
    filename = f"snapshots/{pair}_historical.csv"
    if os.path.isfile(filename):
        with open(filename, "r") as f:
            lines = f.readlines()[1:]  # Skip the header line
            data = [line.strip().split(",") for line in lines]
            return [(float(price), float(bid_liquidity), float(ask_liquidity)) for _, price, bid_liquidity, ask_liquidity, *_ in data]
    return []

def format_pair(pair):
    # Remove spaces and hyphens and convert to uppercase
    return pair.replace(" ", "").replace("-", "").upper()

def fetch_all_pairs():
    endpoint = f"{REST_API_URL}/api/mix/v1/market/contracts"
    params = {'productType': 'umcbl'}
    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        return [contract['symbol'] for contract in data['data']]
    else:
        print("Failed to fetch all pairs. Status Code:", response.status_code)
        return []

def fetch_ticker(symbol):
    endpoint = f"{REST_API_URL}/api/mix/v1/market/ticker"
    params = {'symbol': symbol}
    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        return float(data['data']['last'])
    else:
        print(f"Failed to fetch ticker for {symbol}. Status Code:", response.status_code)
        return None

def fetch_order_book(symbol):
    endpoint = f"{REST_API_URL}/api/mix/v1/market/depth"
    params = {'symbol': symbol, 'limit': DEPTH_LEVEL}
    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        bids = data['data']['bids']  # List of [price, quantity] for bids
        asks = data['data']['asks']  # List of [price, quantity] for asks
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        return best_bid, best_ask, bids, asks
    else:
        print(f"Failed to fetch order book for {symbol}. Status Code:", response.status_code)
        return None, None, None, None

def calculate_order_book_liquidity(bids, asks, price):
    bid_liquidity_usd = sum(float(bid[0]) * float(bid[1]) * price for bid in bids)
    ask_liquidity_usd = sum(float(ask[0]) * float(ask[1]) * price for ask in asks)
    return bid_liquidity_usd, ask_liquidity_usd

def calculate_spread(bids, asks):
    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    return best_ask - best_bid

    spread = calculate_spread(bids, asks)

def calculate_price_deltas(prices):
    deltas = {}
    for delta_minutes in [5, 15, 60]:
        delta_key = f"{delta_minutes}m"
        delta_index = delta_minutes - 1
        if delta_index < len(prices):
            delta = float(prices[-1]) - float(prices[-1 - delta_index])
            deltas[delta_key] = delta
    return deltas

def calculate_percentage_change(previous_value, current_value):
    if previous_value is None or previous_value == 0:
        return None
    return ((current_value - previous_value) / previous_value) * 100

def format_value(value):
    if value is None:
        return "-"
    return f"{value:,.2f}"

def format_percentage_change(percentage_change):
    if percentage_change is None or percentage_change == "-":
        return percentage_change
    color = Fore.GREEN if percentage_change >= 0 else Fore.RED
    return f"{color}{percentage_change:.2f}%{Fore.RESET}"

def predict_action(percentage_change_bid_liquidity):
    if percentage_change_bid_liquidity is None:
        return "Hold"
    elif percentage_change_bid_liquidity > 0:
        return "Buy"
    elif percentage_change_bid_liquidity < 0:
        return "Sell"
    else:
        return "Hold"

def calculate_target_price(ticker_price, action):
    # Set the target percentage change based on the action (you can customize this)
    if action == "Buy":
        target_percentage_change = 2  # 2% increase from current price for buying
    elif action == "Sell":
        target_percentage_change = -1  # 1% decrease from current price for selling
    else:
        return None  # If the action is "Hold," return None

    # Calculate the target price based on the target percentage change
    target_price = ticker_price * (1 + target_percentage_change / 100)
    return target_price

def get_sentiment(pair):
    # Simulate sentiment analysis by generating a random sentiment value
    sentiments = ["Positive", "Neutral", "Negative"]
    return random.choice(sentiments)

def calculate_stop_loss_take_profit(target_price, risk_tolerance):
    if target_price is None:
        return None, None  # Return None if the action is "Hold"

    # Calculate stop-loss and take-profit levels based on target price and risk tolerance
    stop_loss = target_price * (1 - risk_tolerance / 100)
    take_profit = target_price * (1 + risk_tolerance / 100)
    return stop_loss, take_profit

def detect_strong_volume(bids, asks, pair, previous_snapshot_data):
    # Calculate current bid and ask liquidity
    current_bid_liquidity = sum(float(bid[0]) * float(bid[1]) for bid in bids)
    current_ask_liquidity = sum(float(ask[0]) * float(ask[1]) for ask in asks)

    # Calculate average bid and ask liquidity over the window size
    avg_bid_liquidity = sum(float(bid[0]) * float(bid[1]) for bid in bids[-LIQUIDITY_WINDOW_SIZE:]) / LIQUIDITY_WINDOW_SIZE
    avg_ask_liquidity = sum(float(ask[0]) * float(ask[1]) for ask in asks[-LIQUIDITY_WINDOW_SIZE:]) / LIQUIDITY_WINDOW_SIZE

    # Calculate the deviation from the average liquidity
    bid_liquidity_deviation = current_bid_liquidity / avg_bid_liquidity - 1
    ask_liquidity_deviation = current_ask_liquidity / avg_ask_liquidity - 1

    # Get the current timestamp
    current_time = datetime.now()

    # Check if there is an existing cooldown for the pair
    last_alert_time = previous_snapshot_data.get((pair, "alert_time"))

    # Trigger alert if the deviation exceeds the threshold and cooldown has elapsed
    if bid_liquidity_deviation > LIQUIDITY_THRESHOLD and (not last_alert_time or (current_time - last_alert_time) >= timedelta(minutes=5)):
        notification_title = f"Strong Buying Volume Detected for {pair}"
        notification_message = f"Bid Liquidity is {bid_liquidity_deviation:.2%} higher than the average."

        # Show the taskbar notification
        notification.notify(
            title=notification_title,
            message=notification_message,
            app_icon=None,  # You can specify a path to an icon (.ico) file if you want to use a custom icon
            timeout=5       # Notification will automatically close after 5 seconds
        )

        # Update the last alert time to the current time
        previous_snapshot_data[(pair, "alert_time")] = current_time

    elif ask_liquidity_deviation < -LIQUIDITY_THRESHOLD and (not last_alert_time or (current_time - last_alert_time) >= timedelta(minutes=5)):
        notification_title = f"Strong Selling Volume Detected for {pair}"
        notification_message = f"Ask Liquidity is {abs(ask_liquidity_deviation):.2%} lower than the average."

        # Show the taskbar notification
        notification.notify(
            title=notification_title,
            message=notification_message,
            app_icon=None,  # You can specify a path to an icon (.ico) file if you want to use a custom icon
            timeout=5       # Notification will automatically close after 5 seconds
        )

        # Update the last alert time to the current time
        previous_snapshot_data[(pair, "alert_time")] = current_time
    else:
        return  # No strong volume detected or still in cooldown period, exit the function

def main():
    # User Input
    pairs_input = input("Enter pairs to monitor (comma-separated) or type 'all' for all pairs: ")
    if pairs_input.strip().lower() == 'all':
        pairs = ['BTCUSDT_UMCBL']  # Monitor all available pairs
        all_pairs = fetch_all_pairs()
        pairs.extend(all_pairs)
        # Store all pairs in pairs.csv file
        with open('pairs.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Pair'])
            for pair in all_pairs:
                writer.writerow([pair])
    else:
        pairs_list = pairs_input.split(",")
        pairs = [format_pair(pair) + "_UMCBL" for pair in pairs_list]

    timeframe_input = input("Select the timeframe (5m, 15m, 60m): ")
    if timeframe_input not in ['5m', '15m', '60m']:
        print("Invalid timeframe selected. Defaulting to 5m.")
        timeframe = '5m'
    else:
        timeframe = timeframe_input

    real_time_mode = input("Enable real-time mode? (yes/no): ").strip().lower() == "yes"
        # Additional User Inputs
    threshold_input = input("Enter price change threshold percentage: ")
    threshold_percentage = float(threshold_input)

    risk_tolerance_input = input("Enter your risk tolerance percentage: ")
    risk_tolerance = float(risk_tolerance_input)

    print("Starting Bitget Scanner...")

    previous_snapshot_data = {}  # Dictionary to store the previous snapshot data

    # Initialize previous_snapshot_data using historical data from snapshot files
    for pair in pairs:
        historical_data = read_historical_data(pair)
        if historical_data:
            historical_bid_liquidity = [bid_liquidity for _, bid_liquidity, _ in historical_data]
            historical_ask_liquidity = [ask_liquidity for _, _, ask_liquidity in historical_data]
            avg_bid_liquidity = sum(historical_bid_liquidity[-LIQUIDITY_WINDOW_SIZE:]) / LIQUIDITY_WINDOW_SIZE
            avg_ask_liquidity = sum(historical_ask_liquidity[-LIQUIDITY_WINDOW_SIZE:]) / LIQUIDITY_WINDOW_SIZE
            previous_snapshot_data[(pair, "bid")] = avg_bid_liquidity
            previous_snapshot_data[(pair, "ask")] = avg_ask_liquidity

    while True:
        try:
            timestamp = int(time.time())
            data = []

            for pair in pairs:
                ticker_price = fetch_ticker(pair)
                best_bid, best_ask, bids, asks = fetch_order_book(pair)

                if ticker_price is not None and best_bid is not None and best_ask is not None:
                    bid_liquidity_usd, ask_liquidity_usd = calculate_order_book_liquidity(bids, asks, ticker_price)
                    prices = [bid[0] for bid in bids] + [ask[0] for ask in asks]
                    deltas = calculate_price_deltas(prices)

                    # Calculate the spread as the difference between best ask and best bid prices
                    spread = best_ask - best_bid

                    # Calculate percentage change since last snapshot (if available)
                    percentage_change_bid_liquidity = calculate_percentage_change(previous_snapshot_data.get((pair, "bid"), bid_liquidity_usd), bid_liquidity_usd)
                    percentage_change_ask_liquidity = calculate_percentage_change(previous_snapshot_data.get((pair, "ask"), ask_liquidity_usd), ask_liquidity_usd)
                    percentage_change_5m_delta = calculate_percentage_change(previous_snapshot_data.get((pair, "delta"), deltas.get("5m", 0)), deltas.get("5m", 0))

                    # Determine the action (Buy, Sell, or Hold)
                    if percentage_change_bid_liquidity > 0:
                        action = "Buy"
                    elif percentage_change_bid_liquidity < 0:
                        action = "Sell"
                    else:
                        action = "Hold"

                    sentiment = get_sentiment(pair)


                    # Calculate target price based on the action and dynamic range
                    target_price = calculate_target_price(ticker_price, action)
                    stop_loss, take_profit = calculate_stop_loss_take_profit(target_price, risk_tolerance)

                    data.append([
                        pair,
                        ticker_price,
                        format_value(best_bid),
                        format_value(best_ask),
                        format_value(bid_liquidity_usd),
                        format_value(ask_liquidity_usd),
                        format_percentage_change(deltas.get("5m", "-")),
                        format_percentage_change(percentage_change_bid_liquidity),
                        format_percentage_change(percentage_change_ask_liquidity),
                        format_percentage_change(percentage_change_5m_delta),
                        format_value(spread),
                        action,
                        format_value(target_price) if target_price is not None else "-",
                        format_value(stop_loss),
                        format_value(take_profit),
                        sentiment  # Add sentiment here
                    ])

                    # Update previous snapshot data
                    previous_snapshot_data[(pair, "bid")] = bid_liquidity_usd
                    previous_snapshot_data[(pair, "ask")] = ask_liquidity_usd
                    previous_snapshot_data[(pair, "delta")] = deltas.get("5m", 0)

                    # Save data for each pair in separate folder
                    folder_name = f"data/{pair}"
                    os.makedirs(folder_name, exist_ok=True)  # Create the folder if it doesn't exist
                    file_name = f"{folder_name}/{timestamp}.csv"
                    with open(file_name, "w", newline="") as csvfile:
                        writer = csv.writer(csvfile)
                        headers = ["Pair", "Price", "Bid Liquidity (USD)", "Ask Liquidity (USD)", "5m Delta", "% Change (Bid)",
                                   "% Change (Ask)", "% Change (5m)", "Spread", "Action", "Target Price", "Stop-Loss",
                                   "Take-Profit", "Sentiment"]
                        writer.writerow(headers)
                        writer.writerow([
                            pair,
                            ticker_price,
                            bid_liquidity_usd,
                            ask_liquidity_usd,
                            deltas.get("5m", "-"),
                            percentage_change_bid_liquidity,
                            percentage_change_ask_liquidity,
                            percentage_change_5m_delta,
                            spread,
                            action,
                            target_price if target_price is not None else "-",
                            stop_loss if stop_loss is not None else "-",
                            take_profit if take_profit is not None else "-",
                            get_sentiment
                        ])

            headers = ["Pair", "Price", "Best Bid", "Best Ask", "Bid Liquidity (USD)", "Ask Liquidity (USD)",
                       "5m Delta", "% Change (Bid)", "% Change (Ask)", "% Change (5m)", "Spread", "Action",
                       "Target Price", "Stop-Loss", "Take-Profit", "Sentiment"]
            print(tabulate(data, headers=headers, tablefmt="pretty"))

        except KeyboardInterrupt:
            print("Stopping Bitget Scanner...")
            break

if __name__ == "__main__":
    main()


