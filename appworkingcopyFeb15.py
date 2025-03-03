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
    stock_data['Signal Line'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
    # Calculate the Histogram (difference between the MACD and the Signal Line)
    stock_data['Histogram'] = stock_data['MACD'] - stock_data['Signal Line']
    # Get the current MACD, Signal Line, and Histogram
    current_macd = stock_data['MACD'].iloc[-1]
    current_signal_line = stock_data['Signal Line'].iloc[-1]
    current_histogram = stock_data['Histogram'].iloc[-1]
    
    
    #To remove nans from the 20-day and 50-day sma, grab only the most recent 60 days
    stock_data2 = stock_data.iloc[-60:].copy()
    #print("stock data 2, removing 60 earliest datapoints: ", stock_data2[['Close','20-day SMA','50-day SMA']])
    #print(len(stock_data2))
    current_20_day_sma = float(stock_data2['20-day SMA'].iloc[-1])
    current_50_day_sma = float(stock_data2['50-day SMA'].iloc[-1])
    
    #Fixing close data
    stock_data2['Fixed-Close'] = stock_data2['Close'].to_numpy().flatten().tolist()
    print("stock data2 with close fix?: ", stock_data2[['Close','Fixed-Close']])
    
    
    #BUY STRATEGY 1
    #20-day sma > 50-day SMA
    # Add the 'buy_signal' column by comparing '20-day SMA' and '50-day SMA'
    stock_data2['buy_signal'] = stock_data2['20-day SMA'] > stock_data2['50-day SMA']
    #print("stock data 2 with close and buy signals: ", stock_data2[['Close','buy_signal']])
    # Find the most recent 'True' buy signal and get the corresponding date
    most_recent_buy_signal_date = stock_data2[stock_data2['buy_signal'] == True].index[-1]
    current_buy_signal = "BUY 20% max" if stock_data2['buy_signal'].iloc[-1] else "WAIT"
    
    #Sell Strategy 1
    #Sell 50% of current positions when Current price >1.1*20day SMA && number of days since last sell order >=3days
    #Initialize the 'sell-signal' column as False
    stock_data2['sell_signal'] = False

    # Track the last sell signal date
    most_recent_sell_signal_date = None
    # Loop through each row to calculate the sell signal
    for i in range(1, len(stock_data2)):
        # Check if the current day's closing price is greater than 1.1 times the 20-day SMA
        if stock_data2['Fixed-Close'][i] > 1.1 * stock_data2['20-day SMA'][i]:
            # If the number of days since the last sell signal is greater than or equal to 3
            if most_recent_sell_signal_date is None or (stock_data2.index[i] - most_recent_sell_signal_date).days >= 3:
                # Mark this row as a sell signal
                stock_data2['sell_signal'][i] = True
                # Update the last sell signal day
                most_recent_sell_signal_date = stock_data2.index[i]
    current_sell_signal = "sell 50% max" if stock_data2['sell_signal'].iloc[-1] else "WAIT"
    
    #buy and sell signal ping dates
    buy_signal_dates = stock_data2[stock_data2['buy_signal'] == True].index.strftime('%Y-%m-%d').tolist()
    sell_signal_dates = stock_data2[stock_data2['sell_signal'] == True].index.strftime('%Y-%m-%d').tolist()
    
    # Create a dictionary with the data to return
    data = {
        "ticker": ticker,
        "current_price": round(current_price,2),
        "current_20_day_sma": round(current_20_day_sma,2),
        "current_50_day_sma": round(current_50_day_sma,2),
        "most_recent_buy_signal_date": most_recent_buy_signal_date.strftime('%Y-%m-%d'),  # Format date
        "most_recent_sell_signal_date": most_recent_sell_signal_date.strftime('%Y-%m-%d'),  # Format date
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
        "macd": stock_data2['MACD'].values.tolist(),
        "dates": [date.strftime('%Y-%m-%d') for date in stock_data2.index],
        "buy_signal_dates": buy_signal_dates,
        "sell_signal_dates": sell_signal_dates
    }
    #print("Returning data:", data)
    # Return the data 
    return jsonify(data)


# Run the app
if __name__ == "__main__":
    # Run the app with debug mode turned off
    app.run(debug=False, use_reloader=False)
