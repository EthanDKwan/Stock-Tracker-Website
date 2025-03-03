# -*- coding: utf-8 -*-
"""
Created on Sun Feb  2 19:48:27 2025

@author: edkwa
"""
import yfinance as yf
import pandas as pd

from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# Define your route for the homepage
@app.route('/')
def index():
    # You can pass dynamic data here if needed
    return render_template('index.html')

cached_price = None
cached_time = None
CACHE_EXPIRY_TIME = timedelta(minutes=5)

def fetch_stock_data_av_live(ticker):
    global cached_price, cached_time
    if cached_price is not None and cached_time is not None:
        # If the cache is still valid (i.e., not expired)
        if datetime.now() - cached_time < CACHE_EXPIRY_TIME:
            print("Returning cached price")
            return cached_time.strftime("%Y-%m-%d %H:%M:%S"), cached_price
        
    api_key = "41EYMBMQ0JRE5872"  # Your Alpha Vantage API key
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker,
        "apikey": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()
    # Check if the data exists and return the current price and time
    if "Global Quote" in data and "05. price" in data["Global Quote"]:
        price = float(data["Global Quote"]["05. price"])  # Get the price as a float
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current time formatted as datetime string
        return current_time, price
    else:
        return None, None  # Return None if data is missing or invalid

def fetch_stock_data_av_daily(ticker):
    API_KEY = "41EYMBMQ0JRE5872"  # Your Alpha Vantage API key
    url = "https://www.alphavantage.co/query"
    params = {
    "function": "TIME_SERIES_DAILY_ADJUSTED",
    "symbol": ticker,
    "apikey": API_KEY,
    "outputsize": "full"  # "compact" gives only ~100 days; "full" provides full history
    }
    response = requests.get(url,params=params)
    data = response.json()

    if "Time Series (Daily)" not in data:
        raise RuntimeError("Alpha Vantage API error: " + str(data))

    df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
    # Rename columns to match Yahoo Finance format
    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. volume": "Volume"
    })


    df.index = pd.to_datetime(df.index)  # Convert index to datetime format
    df = df.sort_index()  # Ensure it's sorted in chronological order
    df = df.astype(float)
    return df.tail(120)  # Return the most recent 120 days

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    # Fetch current price data using yfinance
    ticker = request.args.get('ticker')  # Get 'ticker' from query params
    
    global cached_price, cached_time
    if cached_price is not None and cached_time is not None:
        # If the cache is still valid (i.e., not expired)
        if datetime.now() - cached_time < CACHE_EXPIRY_TIME:
            print("Returning cached price")
            livetime= cached_time.strftime("%Y-%m-%d %H:%M:%S")
            current_price = cached_price
    else:
        stock_data = yf.download(ticker, period="1d", interval="1m")
        #livetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_price = float(stock_data['Close'].iloc[-1]) 
        
    
    #Alpha Vantage API Call
    #livetime,current_price = fetch_stock_data_av_live(ticker)
    if current_price is None:
        return jsonify({'error': 'Ticker is required'}), 400
    # Get the current stock price
    #current_price = float(stock_data['Close'].iloc[-1])
    

    #Section: Tracking the recent changes to price
    #YFinance API Call for 120 days
    stock_data = yf.download(ticker, period="120d", interval="1d")
    #Alpha Vantage API Call for 120 days
    #stock_data = fetch_stock_data_av_daily(ticker)
    if stock_data.empty:
        return jsonify({'error': 'Ticker is required'}), 400
    # Get the current stock price
    current_price = float(stock_data['Close'].iloc[-1])
    

    stock_data['10-day SMA'] = stock_data['Close'].rolling(window=10).mean()
    stock_data['20-day SMA'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['50-day SMA'] = stock_data['Close'].rolling(window=50).mean()
    
    #STRATEGY 2: MACD to indicate bull/bear trends
    # Calculate the 12-day and 26-day exponential moving averages
    stock_data['12-day EMA'] = stock_data['Close'].ewm(span=12, adjust=False).mean()
    stock_data['26-day EMA'] = stock_data['Close'].ewm(span=26, adjust=False).mean()
    # Calculate the MACD (difference between the 12-day and 26-day EMAs)
    stock_data['MACD'] = stock_data['12-day EMA'] - stock_data['26-day EMA']
    # Calculate the Signal Line (9-day EMA of the MACD)
    stock_data['Signal_Line'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
    # Calculate the Histogram (difference between the MACD and the Signal Line)
    stock_data['Histogram'] = stock_data['MACD'] - stock_data['Signal_Line']
    # Get the current MACD, Signal Line, and Histogram
    current_macd = stock_data['MACD'].iloc[-1]
    current_signal_line = stock_data['Signal_Line'].iloc[-1]
    current_histogram = stock_data['Histogram'].iloc[-1]
    
    
    #To remove nans from the 20-day and 50-day sma, grab only the most recent 60 days
    stock_data2 = stock_data.iloc[-60:].copy()
    #print("stock data 2, removing 60 earliest datapoints: ", stock_data2[['Close','20-day SMA','50-day SMA']])
    #print(len(stock_data2))
    current_20_day_sma = float(stock_data2['20-day SMA'].iloc[-1])
    current_50_day_sma = float(stock_data2['50-day SMA'].iloc[-1])
    
    #Fixing close data
    stock_data2['Fixed-Close'] = stock_data2['Close'].to_numpy().flatten().tolist()
    #print("stock data2 with close fix?: ", stock_data2[['Close','Fixed-Close', '20-day SMA']])
    
    #BUY STRATEGY 1
    #20-day sma > 50-day SMA
    # Add the 'buy_signal' column by comparing '20-day SMA' and '50-day SMA'
    stock_data2['buy_signal'] = stock_data2['20-day SMA'] > stock_data2['50-day SMA']
    #Buy Signal Dates
    buy_signal_dates = stock_data2.index[stock_data2['buy_signal']].tolist()
    if not buy_signal_dates:
        buy_signal_dates = None #the python NoneType means nothing will plot on the frontend
        most_recent_buy_signal_date = None
    else:
        buy_signal_dates = [date.strftime('%Y-%m-%d') for date in buy_signal_dates]
        most_recent_buy_signal_date = stock_data2[stock_data2['buy_signal'] == True].index[-1]
    current_buy_signal = "BUY 20% max" if stock_data2['buy_signal'].iloc[-1] else "WAIT"
    #print("stock data 2 with close and buy signals: ", stock_data2[['Close','buy_signal']])
    #print("buy signal dates : ", buy_signal_dates)
    
    
    #Sell Strategy 1
    #Sell 50% of current positions when Current price >1.1*20day SMA && number of days since last sell order >=3days
    stock_data2['sell_signal'] = False
    most_recent_sell_signal_date = None
    # Loop through each row to calculate the sell signal
    for i in range(1, len(stock_data2)):
        # Check if the current day's closing price is greater than 1.1 times the 20-day SMA
        if stock_data2['Fixed-Close'].iloc[i] > (1.1 * stock_data2['20-day SMA'].iloc[i]):
            # If the number of days since the last sell signal is greater than or equal to 3
            if most_recent_sell_signal_date is None or (stock_data2.index[i] - most_recent_sell_signal_date).days >= 3:
                stock_data2.loc[stock_data2.index[i], 'sell_signal'] = True
                most_recent_sell_signal_date = stock_data2.index[i]
    #Sell Signal Dates
    sell_signal_dates = stock_data2.index[stock_data2['sell_signal']].tolist()
    if not sell_signal_dates:
        sell_signal_dates = None
        most_recent_sell_signal_date = None
    else:
        sell_signal_dates = [date.strftime('%Y-%m-%d') for date in sell_signal_dates]
        most_recent_sell_signal_date = stock_data2[stock_data2['sell_signal'] == True].index[-1]
    current_sell_signal = "sell 50% max" if stock_data2['sell_signal'].iloc[-1] else "WAIT"
    
    print("stock data2 with close fix?: ", stock_data2[['Close','Fixed-Close', '20-day SMA', 'buy_signal','sell_signal']])
    print("buy signal dates : ", buy_signal_dates)
    print("sell signal dates : ", sell_signal_dates)
    
    
    # Create a dictionary with the data to return
    data = {
        #Current price data
        "ticker": ticker,
        "current_price": round(current_price,2),
        "current_20_day_sma": round(current_20_day_sma,2),
        "current_50_day_sma": round(current_50_day_sma,2),
        "most_recent_buy_signal_date": most_recent_buy_signal_date,  # Format date
        "most_recent_sell_signal_date": most_recent_sell_signal_date,  # Format date
        'current_buy_signal': current_buy_signal,
        'current_sell_signal': current_sell_signal,
        'current_macd': round(current_macd,4),
        'current_signal_line': round(current_signal_line,4),
        'current_histogram': round(current_histogram,4),
        
        #60-day for plotting in frontend, returned as lists via jsonify data
        #"dates": stock_data2.index.strftime('%Y-%m-%d').tolist(),
        "closing_prices": stock_data2['Close'].to_numpy().flatten().tolist(),
        "20_day_smas": stock_data2['20-day SMA'].values.tolist(),
        "50_day_smas": stock_data2['50-day SMA'].values.tolist(),
        "histogram": stock_data2['Histogram'].values.tolist(),
        "signal_line": stock_data2['Signal_Line'].values.tolist(),
        "macd": stock_data2['MACD'].values.tolist(),
        "dates": [date.strftime('%Y-%m-%d') for date in stock_data2.index],
        "buy_signal_dates": buy_signal_dates,
        "sell_signal_dates": sell_signal_dates
    }
    print("Returning data:", data)
    # Return the data 
    return jsonify(data)


# Run the app
if __name__ == "__main__":
    # Run the app with debug mode turned off
    app.run(debug=False, use_reloader=False)
