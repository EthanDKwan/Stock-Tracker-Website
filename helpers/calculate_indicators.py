# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:33:51 2025

@author: edkwa
"""

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
    
    stock_data = stock_data.iloc[-60:].copy()
    
    return stock_data