# coding: utf-8

#import http.client
#import httplib
import urllib
import time
import json
import hmac
import hashlib
import base64
import urllib
import logging

from binance.client import Client

import sys
import os
#sys.path.append(os.path.dirname(__file__))

class Binance(object):
    DEBUG = False
    DEBUG_LEVEL = logging.INFO

    def __init__(self, accessKey, secretKey, options = {}):
        self.accessKey = accessKey
        self.secretKey = secretKey

        self.options = options

        self.__client = Client(accessKey, secretKey)

        if (self.DEBUG):
            logging.basicConfig()
            self.logger = logging.getLogger('Binance')
            self.logger.setLevel(self.DEBUG_LEVEL)
            self.requests_log = logging.getLogger("requests.packages.urllib3")
            self.requests_log.setLevel(self.DEBUG_LEVEL)
            self.requests_log.propagate = True
            #http.client.HTTPSConnection.debuglevel = self.DEBUG_LEVEL
            #httplib.HTTPSConnection.debuglevel = self.DEBUG_LEVEL

        self.exchange_info_per_symbol = {}
        self._get_all_exchange_info()

    @property
    def client(self):
        return self.__client
    
    @property
    def exchange_info(self):
        return self.exchange_info_per_symbol

    def _get_all_exchange_info(self):
        exchange_info = self.client.get_exchange_info()

        for symbol_info in exchange_info["symbols"]:
            symbol = symbol_info["symbol"]
            filter_info = {}
            
            filters = symbol_info["filters"]

            for f in filters:
                if f["filterType"] == "PRICE_FILTER":
                    filter_info["price"] = f
                elif f["filterType"] == "LOT_SIZE":
                    filter_info["lot"] = f
            
            self.exchange_info_per_symbol[symbol] = filter_info
        

    def __getattr__(self, attr):
        attrs = ['ticker', 'trade', 'order_book', 'order', 'leverage', 'account'
                , 'send', 'deposit', 'bank_account', 'withdraw', 'borrow', 'transfer']
        
        if attr in attrs:
            #dynamic import module
            moduleName = attr.replace('_', '')
            # get module
            module = __import__('binance_api.' + moduleName)
            module = getattr(module, moduleName)
            #uppercase first letter
            className = attr.title().replace('_', '')
            class_ = getattr(module, className)
            #dynamic create instance of class
            func = class_(self)
            setattr(self, attr, func)
            return func
        else:
            raise AttributeError('Unknown accessor ' + attr)

    """
    def setSignature(self, path, method, arr):
        nonce = "%d" % (round(time.time() * 1000))
        url = 'https://' + self.apiBase + path
        #message = nonce + url + json.dumps(arr)
        if method == ServiceBase.METHOD_GET:
            message = nonce + url + urllib.urlencode(arr)
        else:
            message = nonce + url + json.dumps(arr)
        signature = hmac.new(self.secretKey.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        self.request_headers.update({
                'ACCESS-NONCE': nonce,
                'ACCESS-KEY': self.accessKey,
                'ACCESS-SIGNATURE': signature
            })

        if (self.DEBUG):
            self.logger.info('Set signature...')
            self.logger.debug('\n\tnone: %s\n\turl: %s\n\tmessage: %s\n\tsignature: %s', nonce, url, message, signature)

    def request(self, method, path, params):
        if (method == ServiceBase.METHOD_GET and len(params) > 0):
            path = path + '?' + urllib.urlencode(params)
            params = {};

        data = ''
        self.request_headers = {}
        if (method == ServiceBase.METHOD_POST or method == ServiceBase.METHOD_DELETE):
            data = json.dumps(params).encode('utf-8')
            self.request_headers = {
                'content-type': "application/json"
            }

        self.setSignature(path, method, params)

        #self.client = http.client.HTTPSConnection(self.apiBase)
        self.client = httplib.HTTPSConnection(self.apiBase, timeout=60)
        if (self.DEBUG):
            self.logger.info('Process request...')
        self.client.request(method, path, data, self.request_headers)
        res = self.client.getresponse()
        data = res.read()

        return data.decode("utf-8")
    """
