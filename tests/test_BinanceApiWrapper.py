# coding: utf-8
import unittest
import random
from datetime import datetime
import pytz
import json
from real_trade.api import binance_api

time_offset = 10000*60

# binance api が返してくる json のダミー（driver）をここで、作り、wrapperが正しくデータ変換できているかテストする

class TestBinanceApiWrapper(unittest.TestCase):
    def test_balance(self):
        pass
        
if __name__ == "__main__":
    unittest.main()

