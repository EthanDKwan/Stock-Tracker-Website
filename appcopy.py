import yfinance as yf
from flask import Flask, render_template, jsonify, request
import pandas as pd
import datetime

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio

# Initialize Flask app
app = Flask(__name__)


def get_stock_data(ticker):
    # Download stock data (for the last 60 days for SMA calculations)
    stock_data = yf.download(ticker, period="60d", interval="1d")
    
    # Ensure the necessary data exists
        if stock_data.empty:
            return {
            'error': 'No data available for this ticker.'
        }
   
    # Calculate 20-day and 50-day simple moving averages (SMA)
    stock_data['20-day SMA'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['50-day SMA'] = stock_data['Close'].rolling(window=50).mean()

    stock_data['Prev Close'] = stock_data['Close'].shift(1)  # Previous day's close
    stock_data['Prev SMA 20'] = stock_data['20-day SMA'].shift(1)
    stock_data['Prev SMA 50'] = stock_data['50-day SMA'].shift(1)

    
    # Debug: Check if SMAs are being computed correctly
    #print("Stock Data (with SMAs):")
    #print(stock_data.tail(10))  # Print the last few rows for debugging    

    # Current price (latest closing price)
    Days_Ago = list(range(len(stock_data)))
    #latest_date = stock_data.index[-1].strftime('%Y-%m-%d')
    #Days_Ago = stock_data['Days_Ago'].iloc[-1] if not stock_data['Close'].empty else 0.0
    current_price = stock_data['Close'].iloc[-1] if not stock_data['Close'].empty else 0.0
    last_20_day_sma = stock_data['20-day SMA'].iloc[-1] if not stock_data['20-day SMA'].empty else 0.0
    last_50_day_sma = stock_data['50-day SMA'].iloc[-1] if not stock_data['50-day SMA'].empty else 0.0

    # Ensure we have scalars (not series)
    if isinstance(current_price, pd.Series):
        current_price = current_price.item()
    if isinstance(last_20_day_sma, pd.Series):
        last_20_day_sma = last_20_day_sma.item()
    if isinstance(last_50_day_sma, pd.Series):
        last_50_day_sma = last_50_day_sma.item()

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
    
    # Create the plotly scatter plot
    fig = make_subplots(rows=1, cols=1)
    
    y = stock_data['Close'].values.tolist()
    fig.add_trace(go.Scatter(
        x=Days_Ago,
        y=y,
        name=f'{ticker} Price',
        line=dict(color='black')
    ))
    y = stock_data['20-day SMA'].values.tolist()
    fig.add_trace(go.Scatter(
        x=Days_Ago,
        y=y,
        mode='lines',
        name='20-Day SMA',
        line=dict(color='grey')
    ))
    y = stock_data['50-day SMA'].values.tolist()
    fig.add_trace(go.Scatter(
        x=Days_Ago,
        y=y,
        mode='lines',
        name='50-Day SMA',
        line=dict(color='cyan')
    ))
    # Update layout
    fig.update_layout(
        title=f'{ticker} Stock Price & Moving Averages',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        template='plotly_dark',
        showlegend=True
    )
    
    # Convert plot to HTML and return
    graph_html = pio.to_html(fig, full_html=False)

    # Return data as a dictionary with all required values
    return {
        'graph_html': graph_html,
        'current_price': round(current_price,2),
        'buy_signal': bool(buy_signal),  # Ensuring it's a boolean
        'sell_signal': bool(sell_signal),  # Ensuring it's a boolean
        'timestamp': timestamp,
        'buy_threshold': round(1.1*last_20_day_sma,2),
        'sma_20': round(last_20_day_sma,2),
        'sma_50': round(last_50_day_sma,2)
        #'20_day_sma': last_20_day_sma,
        #'50_day_sma': last_50_day_sma
    }


# Define route for the homepage # THIS is the DEFAULT page look without refreshing
@app.route('/')
def index():
    ticker = 'SPY'  # Or fetch this dynamically based on user input
    data = get_stock_data(ticker)
    
    # Extract the graph HTML from the returned data
    graph_html = data['graph_html']

    # Pass the data to the template for rendering
    return render_template('index.html',graph_html=graph_html)


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
