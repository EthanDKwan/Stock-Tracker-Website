# -*- coding: utf-8 -*-
"""
Created on Sun Feb  2 19:48:27 2025

@author: edkwa
"""
import yfinance as yf
import pandas as pd

from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta, time
import requests

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import atexit
import logging

from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Define your route for the homepage
@app.route('/')
def index():
    # You can pass dynamic data here if needed
    logging.info(f"Index Webpage loaded at {datetime.now()}")
    return render_template('index.html')

# Route for the explore page
@app.route('/explore')
def explore():
    logging.info(f"Explore Webpage loaded at {datetime.now()}")
    return render_template('explore.html')

# Route for the continuous page
@app.route('/continuous')
def continuous():
    return render_template('continuous.html')


cached_price = None
cached_time = None
CACHE_EXPIRY_TIME = timedelta(minutes=5)
CURRENTLY_TRADED_TICKER = "TQQQ"
DEFAULT_TICKER = "SPY"

MARKET_OPEN = time(9,30) #9:30 AM
MARKET_CLOSE = time(16,0) #4:00 PM
interval = 15 #minutes interval for auto-monitor job

load_dotenv()
#email_from = os.getenv('STOCK_TRACKER_EMAIL_FROM')
#email_password = os.getenv('STOCK_TRACKER_EMAIL_PASSWORD')

# Define valid buy and sell signals (adjust as necessary in future)
VALID_BUY_SIGNALS = ["Buy 20% max", "Buy 10% max"]  # Add more as needed
VALID_SELL_SIGNALS = ["Sell 50% max"]


""" #COMMENTING OUT AlphaVantageAPI historical data fetch
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
"""
"""#COMMENTING OUT AlphaVantageAPI daily data fetch
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
"""


def monitor_hard_coded_ticker():
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
                
                send_notification(subject = subject, body = body, to_emial = "edkwan1@gmail.com")
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

def is_market_open():
    now = datetime.now(pytz.timezone('America/New_York')).time()
    return MARKET_OPEN <=now <=MARKET_CLOSE

def monitored_job():
    if not is_market_open():
        logging.info("Market is closed. Skipping this run.")
        return
    logging.info("Market is open. Running auto-monitor at {datetime.now()} ")
    monitor_hard_coded_ticker()


# Configure Scheduler logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Initialize the scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone('America/New_York'))
scheduler.add_job(
    func=monitored_job,
    trigger=CronTrigger(
        day_of_week='mon-fri',  # Monday to Friday
        hour='9-16',            # 9 AM to 3 PM (inclusive)
        minute=f'*/{interval}',             # Start at the top of the hour
        timezone='America/New_York'),
    max_instances=1,  # Prevent overlapping jobs
    id = 'cron_run')

# Start the scheduler
scheduler.start()
logging.info("Scheduler started. Monitoring every {interval} minutes between 9:30AM -4:00 PM, Mon-Fri.")
# Shut down the scheduler
atexit.register(lambda: scheduler.shutdown())
logging.info("Scheduler shutdown handler registered.")
logging.info(f"Scheduler is running: {scheduler.running}")
    

def send_notification(subject, body, to_email):
    """
    Sends an email notification using Gmail SMTP.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_email (str): The recipient's email address.
    """
    try:
        email_from = os.getenv('STOCK_TRACKER_EMAIL_FROM')
        email_password = os.getenv('STOCK_TRACKER_EMAIL_PASSWORD')
        # Validate environment variables
        if not email_from or not email_password:
            logging.error("Email credentials are not set in environment variables.")
            return
        # Create the email
        msg = MIMEMultipart()
        msg['From'] = "Stock Tracker Website <{}>".format(email_from)
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_from, email_password)
            server.sendmail(email_from, to_email, msg.as_string())
        logging.info(f"Email sent to {to_email}: {subject}")
    except smtplib.SMTPAuthenticationError:
        logging.error("Failed to authenticate. Check your email credentials.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")


#Modular helper functions:
def fetch_stock_data(ticker= "SPY", period="120d", interval="1d"):
    """
    Fetch stock data for a given ticker using yfinance.
    
    Args:
        ticker (str): The stock ticker symbol. (make default SPY??)
        period (str): The period of historical data to fetch (default: "120d").
        interval (str): The interval between data points (default: "1d").
    
    Returns:
        pd.DataFrame: Stock data with columns like 'Close', 'High', 'Low', etc.
    
    Raises:
        ValueError: If no data is found for the ticker.
    """
    stock_data = yf.download(ticker, period=period, interval=interval)
    if stock_data.empty:
        raise ValueError(f"No data found for ticker: {ticker}")
    stock_data['Ticker'] = ticker
    
    #ticker = yf.Ticker(ticker)
    #live_price = ticker.info['regularMarketPrice']
    live_price = yf.Ticker(ticker).info['regularMarketPrice']
    stock_data['Live_Price'] = live_price
    return stock_data
    
    
def calculate_indicators(stock_data):
    """
    Calculate technical indicators for the stock data. Facilitates computing indicators for multiple tickers, such as hard-coded, default, and user inputted
    
    Args:
        stock_data (pd.DataFrame): Raw Stock data with columns that include 'Close' closing price
    
    Returns:
        pd.DataFrame: Stock data with added columns for various technical indicators.
    """
    # Calculate SMAs
    stock_data['10-day SMA'] = stock_data['Close'].rolling(window=10).mean()
    stock_data['20-day SMA'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['50-day SMA'] = stock_data['Close'].rolling(window=50).mean()
    
    # Calculate MACD
    stock_data['12-day EMA'] = stock_data['Close'].ewm(span=12, adjust=False).mean()
    stock_data['26-day EMA'] = stock_data['Close'].ewm(span=26, adjust=False).mean()
    stock_data['MACD'] = stock_data['12-day EMA'] - stock_data['26-day EMA']
    stock_data['Signal_Line'] = stock_data['MACD'].ewm(span=9, adjust=False).mean()
    stock_data['Histogram'] = stock_data['MACD'] - stock_data['Signal_Line']
    
    #necessary to remove nans? i.e.
    stock_data = stock_data.iloc[-60:].copy()
    
    return stock_data

def generate_signals(stock_data):
    #print("Inside generate_signals")  # Debugging: Log entry
    
    # Check if stock_data is empty
    if stock_data.empty:
        raise ValueError("Stock data is empty. Cannot generate signals.")
    
    # Check the length of stock_data
    #print("Length of stock_data:", len(stock_data))
    if len(stock_data) < 2:
        raise ValueError("Not enough data to generate signals. At least 2 rows are required.")
    
    # Buy Signal: if 20-day SMA > 50-day SMA, then buy 20% max buying power
    stock_data['buy_signal'] = stock_data['20-day SMA'] > stock_data['50-day SMA']
    #print("Buy signal series:", stock_data['buy_signal'])  # Debugging: Log buy signal series
    #print("Last buy signal value:", stock_data['buy_signal'].iloc[-1])  # Debugging: Log last value
    
    buy_signal_dates = stock_data.index[stock_data['buy_signal']].tolist()
    #print("Buy signal dates:", buy_signal_dates)  # Debugging: Log buy signal dates
    #print("Type of buy_signal_dates:", type(buy_signal_dates))  # Debugging: Log the type
    
    if buy_signal_dates is None or len(buy_signal_dates) == 0:  # Fixed: Explicit check for None or empty list
        buy_signal_dates = None
        most_recent_buy_signal_date = None
    else:
        buy_signal_dates = [date.strftime('%Y-%m-%d') for date in buy_signal_dates]
        most_recent_buy_signal_date = stock_data[stock_data['buy_signal']].index[-1]
    
    # Check the last buy signal value
    if stock_data['buy_signal'].iloc[-1].item() == True:  # Fixed: Use .item() to extract scalar value
        current_buy_signal = "Buy 20% max"
    else:
        current_buy_signal = "WAIT"
    
    # Sell Signal: Current price > 1.1 * 20-day SMA
    live_price = stock_data['Live_Price'].iloc[-1].item()  # Fixed: Use .item() to extract scalar value
    #print("Live price:", live_price)  # Debugging: Log live price
    #print("20-day SMA:", stock_data['20-day SMA'].iloc[-1].item())  # Debugging: Log 20-day SMA
    
    stock_data['sell_signal'] = False
    most_recent_sell_signal_date = None
    for i in range(1, len(stock_data)):
        # Generating historical sell signals based on closing prices
        closing_price = stock_data['Close'].iloc[i].item()
        sma_20_day = stock_data['20-day SMA'].iloc[i]
        #print("20-day sma", sma_20_day)
        #print("20-day sma type: ", type(sma_20_day))
        comparison_value = 1.1 * sma_20_day
        
        #print(f"Row {i}: Closing Price = {closing_price}, 1.1 * 20-day SMA = {comparison_value}")
        #print("Closing type:", type(closing_price))  # Debugging: Log type
        #print("1.1 * 20-day SMA type:", type(comparison_value))  # Debugging: Log type
        
        if closing_price > comparison_value:
            if most_recent_sell_signal_date is None or (stock_data.index[i] - most_recent_sell_signal_date).days >= 3:
                stock_data.loc[stock_data.index[i], 'sell_signal'] = True
                most_recent_sell_signal_date = stock_data.index[i]
    
    # Grabbing sell signal dates to return
    sell_signal_dates = stock_data.index[stock_data['sell_signal']].tolist()
    if not sell_signal_dates:
        sell_signal_dates = None
    else:
        sell_signal_dates = [date.strftime('%Y-%m-%d') for date in sell_signal_dates]
        most_recent_sell_signal_date = stock_data[stock_data['sell_signal'] == True].index[-1]
    
    # Current signals
    current_buy_signal = "Buy 20% max" if stock_data['buy_signal'].iloc[-1].item() else "WAIT"  # Fixed: Use .item()
    if live_price > (1.1 * stock_data['20-day SMA'].iloc[-1].item()):  # Fixed: Use .item()
        current_sell_signal = "Sell 50% max"
        most_recent_sell_signal_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        current_sell_signal = "WAIT"
    
    return {
        "buy_signal_dates": buy_signal_dates,
        "sell_signal_dates": sell_signal_dates,
        "current_buy_signal": current_buy_signal,
        "current_sell_signal": current_sell_signal,
        "most_recent_buy_signal_date": most_recent_buy_signal_date,
        "most_recent_sell_signal_date": most_recent_sell_signal_date
    }
    

def prepare_frontend_data(stock_data, signals):
    """
    Prepare stock data and signals for the frontend.
    
    Args:
        ticker (str): The stock ticker symbol.
        stock_data (pd.DataFrame): Stock data with calculated indicators.
        signals (dict): Buy/sell signals and dates.
    
    Returns:
        dict: A dictionary containing data for the frontend.
    """
    # Extract the most recent 60 days of data for plotting
    stock_data = stock_data.iloc[-60:].copy()
    data = {
        "ticker": stock_data['Ticker'].iloc[-1],
        "current_price": round(stock_data['Live_Price'].iloc[-1],2),
        
        #"current_price": round(stock_data['Close'].iloc[-1], 2),
        "current_20_day_sma": round(stock_data['20-day SMA'].iloc[-1], 2),
        "current_50_day_sma": round(stock_data['50-day SMA'].iloc[-1], 2),
        "current_macd": round(stock_data['MACD'].iloc[-1],4),
        "current_signal_line": round(stock_data['Signal_Line'].iloc[-1],4),
        "current_histogram": round(stock_data['Histogram'].iloc[-1],4),
        
        "macd": stock_data['MACD'].values.tolist(),
        "signal_line": stock_data['Signal_Line'].values.tolist(),
        "histogram": stock_data['Histogram'].values.tolist(),
        "dates": [date.strftime('%Y-%m-%d') for date in stock_data.index],
        "closing_prices": stock_data['Close'].to_numpy().flatten().tolist(),
        "20_day_smas": stock_data['20-day SMA'].values.tolist(),
        "50_day_smas": stock_data['50-day SMA'].values.tolist(),
        **signals  # Include buy/sell signals and dates
    }
    #print("Returning data:", data)
    # Return the data 
    return data


@app.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    """ Handle on-demand requests for stock data (Goals 3+4)"""
    ticker = request.args.get('ticker', DEFAULT_TICKER) # Get ticker from frontend query
    try:
        stock_data = fetch_stock_data(ticker)
        stock_data = calculate_indicators(stock_data)
        #print("Fetched stock data + indicators:", stock_data.head())
        signals = generate_signals(stock_data)
        #print("Calculated signals (type):", type(signals))
        print ("Generated signals: ", signals)
        frontend_data = prepare_frontend_data(stock_data, signals)
        #print("Frontend data (type): ", type(frontend_data))
        #print("Frontend data: ", frontend_data)
        return jsonify(frontend_data)
    except Exception as e:
        print(f"Error processing ticker {ticker}: {e}")
        return jsonify ({'error': str(e)}), 400


# Run the app
if __name__ == "__main__":
    # Run the app with debug mode turned off
    app.run(debug=False, use_reloader=False)

