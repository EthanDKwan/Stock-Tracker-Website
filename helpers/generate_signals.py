# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:34:38 2025

@author: edkwa
"""

from datetime import datetime

#Includes Buy/Sell Signal definitions

def generate_signals(stock_data):
    # Check if stock_data is empty
    if stock_data.empty:
        raise ValueError("Stock data is empty. Cannot generate signals.")
    
    if len(stock_data) < 2:
        raise ValueError("Not enough data to generate signals. At least 2 rows are required.")
    
    # Buy Signal: if 20-day SMA > 50-day SMA, then buy 20% max buying power
    stock_data['buy_signal'] = stock_data['20-day SMA'] > stock_data['50-day SMA']
    buy_signal_dates = stock_data.index[stock_data['buy_signal']].tolist()
    
    if buy_signal_dates is None or len(buy_signal_dates) == 0:
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
    live_price = stock_data['Live_Price'].iloc[-1].item()
    
    stock_data['sell_signal'] = False
    most_recent_sell_signal_date = None
    for i in range(1, len(stock_data)):
        # Generating historical sell signals based on closing prices
        closing_price = stock_data['Close'].iloc[i].item()
        sma_20_day = stock_data['20-day SMA'].iloc[i]
        comparison_value = 1.1 * sma_20_day
        
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