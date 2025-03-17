# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:47:34 2025

@author: edkwa
"""
from helpers.is_market_open import is_market_open
from helpers.monitor_hard_coded_ticker import monitor_hard_coded_ticker

import logging

def monitored_job():
    if not is_market_open():
        logging.info("Market is closed. Skipping this run.")
        return
    logging.info("Market is open. Auto-monitor running as of {datetime.now()} ")
    monitor_hard_coded_ticker()