# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:35:52 2025

@author: edkwa
"""

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
    return data