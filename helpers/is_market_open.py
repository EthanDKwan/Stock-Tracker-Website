# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 16:46:14 2025

@author: edkwa
"""
from datetime import datetime, time
import pytz

def is_market_open():
    MARKET_OPEN = time(9,30) #9:30 AM
    MARKET_CLOSE = time(16,0) #4:00 PM
    now = datetime.now(pytz.timezone('America/New_York')).time()
    return MARKET_OPEN <=now <=MARKET_CLOSE