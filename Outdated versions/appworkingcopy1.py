# -*- coding: utf-8 -*-
"""
Created on Sun Feb  2 19:48:27 2025

@author: edkwa
"""
import yfinance as yf

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Define your route for the homepage
@app.route('/')
def index():
    # You can pass dynamic data here if needed
    return render_template('index.html')

@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    # Fetch current price data using yfinance
    ticker = request.args.get('ticker')  # Get 'ticker' from query params
    stock_data = yf.download(ticker, period="1d", interval="1m")
    if stock_data.empty:
        return jsonify({'error': 'Ticker is required'}), 400
    # Get the current stock price
    current_price = float(stock_data['Close'].iloc[-1])
    

    #NEXT section: for tracking the recent changes to price
    stock_data = yf.download(ticker, period="120d", interval="1d")
    if stock_data.empty:
        return jsonify({'error': 'Ticker is required'}), 400
    # Calculate the 20-day and 50-day SMA
    stock_data['20-day SMA'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['50-day SMA'] = stock_data['Close'].rolling(window=50).mean()
    
    #To remove nans from the 20-day and 50-day sma, grab only the most recent 60 days
    stock_data2 = stock_data.iloc[-60:].copy()
    print("stock data 2, removing 60 earliest datapoints: ", stock_data2[['Close','20-day SMA','50-day SMA']])
    print(len(stock_data2))
    current_20_day_sma = float(stock_data2['20-day SMA'].iloc[-1])
    current_50_day_sma = float(stock_data2['50-day SMA'].iloc[-1])
    
    
    # Add the 'buy_signal' column by comparing '20-day SMA' and '50-day SMA'
    stock_data2['buy_signal'] = stock_data2['20-day SMA'] > stock_data2['50-day SMA']
    print("stock data 2 buy signals: ", stock_data2[['Close','buy_signal']])
    # Find the most recent 'True' buy signal and get the corresponding date
    most_recent_buy_signal_date = stock_data2[stock_data2['buy_signal'] == True].index[-1]
    current_buy_signal = "BUY 20% max" if stock_data2['buy_signal'].iloc[-1] else "WAIT"
    
    
    
    # Create a dictionary with the data to return
    data = {
        "ticker": ticker,
        "current_price": round(current_price,2),
        "current_20_day_sma": round(current_20_day_sma,2),
        "current_50_day_sma": round(current_50_day_sma,2),
        'most_recent_buy_signal_date': most_recent_buy_signal_date.strftime('%Y-%m-%d'),  # Format date
        'current_buy_signal': current_buy_signal
    }
    # Return the data 
    return jsonify(data)


# Run the app
if __name__ == "__main__":
    # Run the app with debug mode turned off
    app.run(debug=False, use_reloader=False)
