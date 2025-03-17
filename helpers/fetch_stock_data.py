# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:31:23 2025

@author: edkwa
"""
import yfinance as yf

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
    
    live_price = yf.Ticker(ticker).info['regularMarketPrice']
    stock_data['Live_Price'] = live_price
    return stock_data