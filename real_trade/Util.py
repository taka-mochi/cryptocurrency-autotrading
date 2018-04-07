# coding: utf-8
import math
from datetime import datetime
from datetime import timedelta
import pytz

TIMESTAMP_BASEDATE = datetime(year=1970,month=1,day=1,tzinfo=pytz.utc)

class TimeUtil:
    @staticmethod
    def timestamp_utc(timeaware_datetime):
        diff = timeaware_datetime - TIMESTAMP_BASEDATE
        return diff.total_seconds()

    @staticmethod
    def now_utc():
        return datetime.now(pytz.utc)

    @staticmethod
    def now_timestamp_utc():
        return TimeUtil.timestamp_utc(TimeUtil.now_utc())

    @staticmethod
    def fromutctimestamp(timestamp):
        return TIMESTAMP_BASEDATE + timedelta(seconds=timestamp)

class BitcoinUtil:
    @staticmethod
    def roundBTCby1satoshi(btc):
        return BitcoinUtil.roundBTC(btc, len("00000001"))

    @staticmethod
    def roundBTC(btc, roundDigitCountLessThan1):
        if roundDigitCountLessThan1 <= 0:
            return btc

        # 1satoshi: 0.00000001
        btc_str = "%.8f" % btc
        pos = btc_str.find(".")
        if pos < 0:
            #小数点以下なし
            return btc
        
        upper_part = btc_str[0:pos]
        lower_part = btc_str[pos+1:]

        # 指定された小数点以下の桁数
        len_of_less_than_1 = roundDigitCountLessThan1

        if len(lower_part) > len_of_less_than_1:
            lower_part = lower_part[0:len_of_less_than_1]

        if upper_part == "":
            upper_part = "0"

        return float(upper_part + "." + lower_part)
