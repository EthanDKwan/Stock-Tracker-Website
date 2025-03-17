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
    
    #print(stock_data.head(60))
    
    print("Columns in stock_data:", stock_data.columns)
    
    print(stock_data[['Close']].head(30))  # Show first 30 rows

    # Calculate 20-day and 50-day simple moving averages (SMA)
    stock_data['20-day SMA'] = stock_data['Close'].rolling(window=20, min_periods=20).mean()
    stock_data['50-day SMA'] = stock_data['Close'].rolling(window=50, min_periods=50).mean()
    
    
    #print(stock_data[['Close', '20-day SMA', '50-day SMA']].iloc[19:60])  # Print 20-60 rows
    print(stock_data[['20-day SMA']].head(30))  # See if it's being calculated
    print(stock_data[['50-day SMA']].head(30))  # See if it's being calculated
    print(stock_data.index)

    #debug
    #print(stock_data[['20-day SMA', '50-day SMA']].head())
    

    if '20-day SMA' not in stock_data.columns or '50-day SMA' not in stock_data.columns:
        #print("Error: SMA columns were not created!")
        return {"error": "SMA calculation failed"}, 400
    
    #drop nans
    #stock_data = stock_data.dropna(subset=['20-day SMA', '50-day SMA'])
    
    if stock_data.empty:
        return {"error": "Not enough data for SMA calculation"}, 400
    
    stock_data['20-day SMA'].fillna(0, inplace=True)
    stock_data['50-day SMA'].fillna(0, inplace=True)

    
    stock_data['Prev Close'] = stock_data['Close'].shift(1)  # Previous day's close
    stock_data['Prev SMA 20'] = stock_data['20-day SMA'].shift(1)
    stock_data['Prev SMA 50'] = stock_data['50-day SMA'].shift(1)

    
    # Debug: Check if SMAs are being computed correctly
    #print("Stock Data (with SMAs):")
    #print(stock_data.tail(10))  # Print the last few rows for debugging    
   
    # Ensure both Series are aligned
    stock_data[['Prev SMA 20', 'Prev SMA 50']] = stock_data[['Prev SMA 20', 'Prev SMA 50']].fillna(0)



    # Identify all buy signals: when 20-day SMA crosses above 50-day SMA
    stock_data['Buy Signal'] = (stock_data['Prev SMA 20'] < stock_data['Prev SMA 50']) & (stock_data['20-day SMA'] > stock_data['50-day SMA'])

    # Identify sell signals: when current price > 1.1 * 20-day SMA
    stock_data['Sell Signal'] = stock_data['Close'] > (1.1 * stock_data['20-day SMA'])
    
    # Get last buy/sell signal dates
    buy_dates = stock_data[stock_data['Buy Signal']].index
    sell_dates = stock_data[stock_data['Sell Signal']].index

    last_buy_date = "N/A"
    last_sell_date = "N/A"

    if len(buy_dates) > 0:
        for i in range(len(buy_dates) - 1, -1, -1):  # Iterate backwards to find valid buy
            if (stock_data.index[-1] - buy_dates[i]).days > 1:  # More than 1 day ago
                last_buy_date = buy_dates[i].strftime('%Y-%m-%d')
                break

    if len(sell_dates) > 0:
        for i in range(len(sell_dates) - 1, -1, -1):  # Iterate backwards to find valid sell
            if (stock_data.index[-1] - sell_dates[i]).days > 3:  # More than 3 days ago
                last_sell_date = sell_dates[i].strftime('%Y-%m-%d')
                break

    # Current price (latest closing price)
    #Days_Ago = list(range(len(stock_data)))
    
    current_price = stock_data['Close'].iloc[-1] if not stock_data['Close'].empty else 0.0
    last_20_day_sma = stock_data['20-day SMA'].iloc[-1] if not stock_data['20-day SMA'].empty else 0.0
    last_50_day_sma = stock_data['50-day SMA'].iloc[-1] if not stock_data['50-day SMA'].empty else 0.0

    # Ensure we have scalars (not series)
    #if isinstance(current_price, pd.Series):
    #    current_price = current_price.item()
    #if isinstance(last_20_day_sma, pd.Series):
    #    last_20_day_sma = last_20_day_sma.item()
    #if isinstance(last_50_day_sma, pd.Series):
    #    last_50_day_sma = last_50_day_sma.item()

    # Calculate buy and sell signals based on conditions
    buy_signal = False
    sell_signal = False

    # Buy condition: 20-day SMA > 50-day SMA
    if last_20_day_sma > last_50_day_sma:
        buy_signal = True

    # Sell condition: Current price > 1.1 * 20-day SMA
    if current_price > 1.1 * last_20_day_sma:
        sell_signal = True

    # Current timestamp
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    data = {'current_price': round(current_price,2),
    'buy_signal': bool(buy_signal),  # Ensuring it's a boolean
    'sell_signal': bool(sell_signal),  # Ensuring it's a boolean
    'timestamp': timestamp,
    'buy_threshold': round(1.1*last_20_day_sma,2),
    'sma_20': round(last_20_day_sma,2),
    'sma_50': round(last_50_day_sma,2),
    'last_buy_date':last_buy_date,
    'last_sell_date':last_sell_date
    #'20_day_sma': last_20_day_sma,
    #'50_day_sma': last_50_day_sma
    }
    
    print(data)

    # Return data as a dictionary with all required values
    return jsonify(data)
#{       'current_price': round(current_price,2),
 #       'buy_signal': bool(buy_signal),  # Ensuring it's a boolean
  #      'sell_signal': bool(sell_signal),  # Ensuring it's a boolean
   #     'timestamp': timestamp,
    #    'buy_threshold': round(1.1*last_20_day_sma,2),
     #   'sma_20': round(last_20_day_sma,2),
      #  'sma_50': round(last_50_day_sma,2),
       # 'last_buy_date':last_buy_date,
        #'last_sell_date':last_sell_date
        #'20_day_sma': last_20_day_sma,
        #'50_day_sma': last_50_day_sma
    #})


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
