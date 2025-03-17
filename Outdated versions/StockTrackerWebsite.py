# -*- coding: utf-8 -*-
"""
Created on Sun Feb  2 13:32:07 2025

@author: edkwa
"""

from flask import Flask, jsonify, render_template
import yfinance as yf
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# Configuration
STOCK_SYMBOL = "SPY"  # Change this to track different indices
HISTORY_FILE = "stock_history.csv"

# Function to fetch real-time stock data
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    df = stock.history(period="3mo")
    
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["SMA_50"] = df["Close"].rolling(window=50).mean()

    # Save daily closing price
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(HISTORY_FILE) or today not in open(HISTORY_FILE).read():
        df.tail(1)[["Close", "SMA_20", "SMA_50"]].to_csv(HISTORY_FILE, mode='a', header=not os.path.exists(HISTORY_FILE))
    
    return df

@app.route('/data')
def fetch_data():
    df = get_stock_data(STOCK_SYMBOL)
    latest = df.iloc[-1]
    return jsonify({
        "symbol": STOCK_SYMBOL,
        "date": latest.name.strftime("%Y-%m-%d"),
        "price": round(latest["Close"], 2),
        "sma_20": round(latest["SMA_20"], 2),
        "sma_50": round(latest["SMA_50"], 2)
    })

@app.route('/')
def home():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
