# -*- coding: utf-8 -*-
"""
Created on Sun Feb  2 19:48:27 2025

@author: edkwa
"""

import yfinance as yf
from flask import Flask, render_template, jsonify, request
import pandas as pd
import datetime


# Initialize Flask app
app = Flask(__name__)


def get_stock_data(ticker):
    # Download stock data (for the last 60 days for SMA calculations)
    stock_data = yf.download(ticker, period="120d", interval="1d")
    print("Data-length: ", len(stock_data))
    
    # Ensure the necessary data exists
    if stock_data.empty:
        return {
            'error': 'No data available for this ticker.'
        }
    
    # Keep only the last 60 days for analysis
    stock_data['20-day SMA'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['50-day SMA'] = stock_data['Close'].rolling(window=50).mean()
    
    # Replace NaNs with 0 (for incomplete SMA calculations at the beginning)
    stock_data.fillna(0, inplace=True)


    # Drop the first 60 days to keep only the last 60 days of analysis
    stock_data = stock_data.iloc[-60:].copy()
    print("Data-length after slicing: ", len(stock_data))
    print("Stock data after slicing", stock_data)
    
    # Identifying Buy Signals
    #stock_data['Buy Signal'] = (stock_data['20-day SMA'] > stock_data['50-day SMA'])
    # Initialize lists for signals
    buy_signals = [False]  # No buy signal on the first day (it has no previous data)
    sell_signals = [False]  # No sell signal on the first day either

    last_buy_signal = -float('inf')
    last_sell_signal = -float('inf')

    # Loop through the stock data starting from the second day
    for i in range(1, len(stock_data)):
        current_row = stock_data.iloc[i]
        previous_row = stock_data.iloc[i - 1]

        # Buy signal: 20-day SMA crosses above 50-day SMA, and 1 day has passed since last buy signal
        buy_condition = (current_row['20-day SMA'] > current_row['50-day SMA']) and (previous_row['20-day SMA'] <= previous_row['50-day SMA'])
        if buy_condition and (i - last_buy_signal) > 1:
            buy_signals.append(True)
            last_buy_signal = i
        else:
            buy_signals.append(False)

        # Sell signal: current price is greater than 1.1 times the 20-day SMA, and 3 days have passed since last sell signal
        sell_condition = (current_row['Close'] > 1.1 * current_row['20-day SMA']) and (previous_row['Close'] <= 1.1 * previous_row['20-day SMA'])
        if sell_condition and (i - last_sell_signal) > 3:
            sell_signals.append(True)
            last_sell_signal = i
        else:
            sell_signals.append(False)

    # Add signals as new columns to the stock_data DataFrame
    stock_data['Buy Signal'] = buy_signals
    stock_data['Sell Signal'] = sell_signals

    # Collect buy/sell signal dates
    buy_signal_dates = stock_data[stock_data['Buy Signal']].index.tolist()
    sell_signal_dates = stock_data[stock_data['Sell Signal']].index.tolist()

    # Return the result in a structured format
    result = {
        'current_price': stock_data['Close'].iloc[-1],
        'current_buy_signal': stock_data['Buy Signal'].iloc[-1],
        'current_sell_signal': stock_data['Sell Signal'].iloc[-1],
        'buy_signal_dates': buy_signal_dates,
        'sell_signal_dates': sell_signal_dates,
        '20_day_sma': stock_data['20-day SMA'].iloc[-1],
        '50_day_sma': stock_data['50-day SMA'].iloc[-1],
        #'current_date': stock_data.index[-1].strftime('%Y-%m-%d')
    }

    return result


# Define route for the homepage # THIS is the DEFAULT page look without refreshing
@app.route('/')
def index():
    ticker = 'SPY'  # Or fetch this dynamically based on user input
    data = get_stock_data(ticker)
    
    # Pass the data to the template for rendering
    return render_template('index.html', data = data)


# Define route to get stock data (AJAX call from frontend) 
#This is the updating page look and data per 60 second CALL
@app.route('/get_stock_data')
def stock_data():
    ticker = request.args.get('ticker', default='SPY', type=str)  # Default ticker is SPY# You can change this or make it dynamic in the future
    data = get_stock_data(ticker)
    return jsonify(data)

# Run the app
if __name__ == "__main__":
    # Run the app with debug mode turned off
    app.run(debug=False, use_reloader=False)
