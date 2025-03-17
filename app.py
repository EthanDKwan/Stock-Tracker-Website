# -*- coding: utf-8 -*-
"""
Created on Sun Feb  2 19:48:27 2025

@author: edkwa
"""
from flask import Flask, render_template, request, jsonify

#Helper functions
from helpers.fetch_stock_data import fetch_stock_data
from helpers.calculate_indicators import calculate_indicators
from helpers.generate_signals import generate_signals
from helpers.prepare_frontend_data import prepare_frontend_data
from helpers.monitored_job import monitored_job

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
import atexit
import logging

app = Flask(__name__)

DEFAULT_TICKER = "SPY"
interval = 15 #minutes interval for auto-monitor job

#Initialize the scheduler
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        #print ("Generated signals: ", signals)
        frontend_data = prepare_frontend_data(stock_data, signals)
        #print("Frontend data (type): ", type(frontend_data))
        #print("Frontend data: ", frontend_data)
        return jsonify(frontend_data)
    except Exception as e:
        print(f"Error processing ticker {ticker}: {e}")
        return jsonify ({'error': str(e)}), 400

# Define your route for the homepage
@app.route('/')
def index():
    # You can pass dynamic data here if needed
    logging.info(f"Webpage loaded at {datetime.now()}")
    return render_template('continuous.html')

# Route for the explore page
@app.route('/explore')
def explore():
    logging.info(f"Explore Webpage loaded at {datetime.now()}")
    return render_template('explore.html')

# Route for the continuous page
@app.route('/continuous')
def continuous():
    return render_template('continuous.html')

# Run the app
if __name__ == "__main__":
    # Run the app with debug mode turned off
    app.run(debug=False, use_reloader=False)