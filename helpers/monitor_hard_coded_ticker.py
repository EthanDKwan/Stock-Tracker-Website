# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:37:45 2025

@author: edkwa
"""

#Helper functions
from helpers.fetch_stock_data import fetch_stock_data
from helpers.calculate_indicators import calculate_indicators
from helpers.generate_signals import generate_signals
from helpers.send_notification import send_notification

import logging
import yfinance as yf
from datetime import datetime


#Includes buy/sell signal definition
def monitor_hard_coded_ticker():

    CURRENTLY_TRADED_TICKER = "TQQQ"
    # Define valid buy and sell signals
    VALID_BUY_SIGNALS = ["Buy 20% max", "Buy 10% max"]  # Add more as needed
    VALID_SELL_SIGNALS = ["Sell 50% max"]
    
    
    
    logging.info(f"Monitoring {CURRENTLY_TRADED_TICKER} at {datetime.now()}")
    try:
        # Step 1: Fetch stock data
        stock_data = fetch_stock_data(CURRENTLY_TRADED_TICKER)

        # Step 2: Calculate indicators
        stock_data = calculate_indicators(stock_data)

        # Step 3: Generate signals
        signals = generate_signals(stock_data)

        # Step 4: Check for buy signals
        current_buy_signal = signals.get("current_buy_signal")
        if current_buy_signal != "WAIT":
            if current_buy_signal in VALID_BUY_SIGNALS:
                logging.info(f"BUY signal triggered for {CURRENTLY_TRADED_TICKER}: {current_buy_signal}")
                
                
                most_recent_row = stock_data.iloc[-1]
                ticker = most_recent_row['Ticker']
                price = most_recent_row['Price']
                sma_20 = most_recent_row['20-day SMA']
                sma_50 = most_recent_row['50-day SMA']
                
                # Customize the email subject and body
                subject = f"Stock Tracker Website: A {current_buy_signal} Signal for {CURRENTLY_TRADED_TICKER}"
                body = (
                f"A BUY signal has been detected for {ticker}.\n\n"
                f"Recommendation: {current_buy_signal}\n"
                f"20-Day SMA (${sma_20:.2f}) > 50-Day SMA (${sma_50:.2f})\n"
                f"Current Price: ${price:.2f}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Please review accordingly."
                )
                
                send_notification(subject = subject, body = body, to_email = "edkwan1@gmail.com")
            else:
                logging.error(f"Unexpected buy signal for {CURRENTLY_TRADED_TICKER}: {current_buy_signal}")

        # Step 5: Check for sell signals
        current_sell_signal = signals.get("current_sell_signal")
        if current_sell_signal != "WAIT":
            if current_sell_signal in VALID_SELL_SIGNALS:
                logging.info(f"SELL signal triggered for {CURRENTLY_TRADED_TICKER}: {current_sell_signal}")
                
                most_recent_row = stock_data.iloc[-1]
                ticker = most_recent_row['Ticker']
                price = most_recent_row['Price']
                sma_20 = most_recent_row['20-day SMA']
                
                # Customize the email subject and body
                subject = f"Stock Tracker Website: A {current_sell_signal} Signal for {CURRENTLY_TRADED_TICKER}"
                body = (
                f"A SELL signal has been detected for {ticker}.\n\n"
                f"Recommendation: {current_sell_signal}\n"
                f"Current Price (${price:.2f}) > 110% x 20-Day SMA (${sma_20:.2f})\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Please review accordingly."
                )
                
                send_notification(subject = subject, body = body, to_email = "edkwan1@gmail.com")
            else:
                logging.error(f"Unexpected sell signal for {CURRENTLY_TRADED_TICKER}: {current_sell_signal}")

    except yf.YFinanceError as e:
        logging.error(f"Failed to fetch data for {CURRENTLY_TRADED_TICKER}: {e}")
    except KeyError as e:
        logging.error(f"Missing expected key in data: {e}")
    except ValueError as e:
        logging.error(f"Error in indicator calculation: {e}")
    except Exception as e:
        logging.error(f"Unexpected error monitoring {CURRENTLY_TRADED_TICKER}: {e}")