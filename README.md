<h1 align="center">
  BitGet Scanner - Real-Time Cryptocurrency Trading Analysis
</h1>

<p align="center">
  <img src="https://img.shields.io/github/DaCryptoRaccoon/Bitget-Scanner/blob/main/License">
  <img src="https://img.shields.io/github/languages/top/DaCryptoRaccoon/Bitget-Scanner">
</p>

<p align="center">
  BitGet Scanner is a Python-based script that provides real-time analysis of cryptocurrency trading pairs on the BitGet exchange. The script fetches market data, calculates liquidity, and predicts possible trading actions. It also sends notifications when strong buying or selling volumes are detected.
</p>

## Prerequisites

Before running the BitGet Scanner, make sure you have the following requirements installed:

- Python 3.x+

The required Python packages can be installed using the following command:

```bash
pip install tabulate colorama plyer requests
```
Getting Started
🚀 Clone the repository or download the script files to your local machine.

📂 Create a .env file in the same directory as the script files and add the following environment variables:
```bash
makefile
Copy code
API_KEY=your_bitget_api_key
PASSPHRASE=your_bitget_passphrase
SECRET_KEY=your_bitget_secret_key
Replace your_bitget_api_key, your_bitget_passphrase, and your_bitget_secret_key with your actual API credentials from BitGet.
```
⚙️ Run the BitGet Scanner script using the following command:

```bash

python bitget_scanner.py

```
Configuration
Upon running the script, you will be prompted to enter the pairs to monitor. You can enter a comma-separated list of trading pairs or type 'all' to monitor all available pairs.

Next, select the timeframe for price change calculations. Available options are '5m', '15m', and '60m'. If an invalid option is selected, the script will default to '5m'.

Choose whether to enable real-time mode. If 'yes', the script will fetch real-time market data and perform analysis. If 'no', the script will use historical data from CSV files in the 'snapshots' folder.

Additional User Inputs:

Enter the price change threshold percentage (threshold_percentage): Set the minimum price change percentage to trigger a trading action.
Enter your risk tolerance percentage (risk_tolerance): Set the percentage of risk tolerance for stop-loss and take-profit levels.
Features
Market Data and Liquidity Analysis:

The script fetches real-time market data, including the best bid, best ask, bid liquidity, and ask liquidity for the selected trading pairs.
It calculates the spread as the difference between the best ask and best bid prices.
Liquidity is calculated based on the sum of bid and ask liquidity for a given price level.
Trading Action Prediction:

The script predicts the trading action (Buy, Sell, or Hold) based on the percentage change in bid liquidity.
Target Price Calculation:

The target price is calculated based on the predicted trading action and a dynamic range.
Stop-Loss and Take-Profit Calculation:

The script calculates stop-loss and take-profit levels based on the target price and the risk tolerance percentage.
Sentiment Analysis:

The script simulates sentiment analysis by generating a random sentiment value (Positive, Neutral, or Negative).
Strong Volume Detection:

The script detects strong buying or selling volumes if the bid or ask liquidity significantly deviates from the average liquidity.

Notes
Trading cryptocurrencies involves risks, and this script is for educational and informational purposes only. It does not provide financial advice or make actual trades.
The script uses the Plyer library to send desktop notifications for strong buying or selling volumes. You can customize the notification messages and icons as needed.
Historical data for liquidity is stored in CSV files in the 'snapshots' folder. You can modify the frequency of data snapshots based on your trading strategy.

Disclaimer
The use of this script is at your own risk. The authors of this script are not responsible for any financial losses or damages incurred by using this script or following the trading decisions based on its output.

Always exercise caution and perform thorough research before making any trading decisions in the cryptocurrency market.

Support
For any questions or issues related to the BitGet Scanner, please open an issue on the GitHub repository.

License
This project is licensed under the MIT License. See the 'LICENSE' file for more details.

<p align="center">
  Made with ❤️ by DaCryptoRaccoon
</p>
```
