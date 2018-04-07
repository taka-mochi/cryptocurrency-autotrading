# coding: utf-8
import unittest
from real_trade.Util import BitcoinUtil
from real_trade.Util import TimeUtil

from datetime import datetime
from datetime import timedelta
import pytz

class TestUtil(unittest.TestCase):
    def test_timeutil(self):
        t = datetime(year=2017, month=8, day=25, tzinfo=pytz.utc)
        diff = t - datetime(year=1970, month=1, day=1, tzinfo=pytz.utc)

        self.assertEqual(diff.total_seconds(), TimeUtil.timestamp_utc(t))

        diff = 1920
        got = TimeUtil.fromutctimestamp(float(diff))
        target = datetime(year=1970,month=1,day=1, tzinfo=pytz.utc) + timedelta(seconds=diff)
        self.assertEqual(got, target)

    def test_roundBtc(self):
        self.assertEqual(1, BitcoinUtil.roundBTCby1satoshi(1))
        self.assertEqual("1.2345", str(BitcoinUtil.roundBTCby1satoshi(1.2345)))
        self.assertEqual("1.00100001", str(BitcoinUtil.roundBTCby1satoshi(1.0010000101)))
        self.assertEqual("1.0010001", str(BitcoinUtil.roundBTCby1satoshi(1.0010001001)))

        self.assertEqual("1.2", str(BitcoinUtil.roundBTC(1.2345, 1)))
        self.assertEqual("1.23", str(BitcoinUtil.roundBTC(1.2345, 2)))
        self.assertEqual("1.234", str(BitcoinUtil.roundBTC(1.2345, 3)))
        self.assertEqual("1.2345", str(BitcoinUtil.roundBTC(1.2345, 4)))
        self.assertEqual("1.2345", str(BitcoinUtil.roundBTC(1.2345, 5)))

        self.assertEqual(3.2e-6, BitcoinUtil.roundBTCby1satoshi(3.2e-6))
        self.assertEqual(3.0e-8, BitcoinUtil.roundBTCby1satoshi(3.2e-8))

if __name__ == "__main__":
    unittest.main()

