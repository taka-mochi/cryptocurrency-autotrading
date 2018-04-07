# coding: utf-8

import pybitflyer

class Bitflyer(object):
    def __init__(self, accessKey, secretKey):
        self.accessKey = accessKey
        self.secretkey = secretKey

        self.api = pybitflyer.API(api_key=accessKey, api_secret=secretKey)

    def __getattr__(self, attr):
        attrs = ['order', 'leverage', 'account', 'bank_account']

        if attr in attrs:
            #dynamic import module
            moduleName = attr.replace('_', '')
            module = __import__('bitflyer.' + moduleName)
            #uppercase first letter
            className = attr.title().replace('_', '')
            module = getattr(module, moduleName)
            class_ = getattr(module, className)
            #dynamic create instance of class
            func = class_(self)
            setattr(self, attr, func)
            return func
        else:
            raise AttributeError('Unknown accessor ' + attr)

