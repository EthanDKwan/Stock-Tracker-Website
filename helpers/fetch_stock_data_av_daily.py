# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:55:14 2025

@author: edkwa
"""
import requests
import pandas as pd

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