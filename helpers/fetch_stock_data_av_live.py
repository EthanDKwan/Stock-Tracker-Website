# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:56:28 2025

@author: edkwa
"""

from datetime import datetime
import requests

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