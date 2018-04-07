from servicebase import ServiceBase

class Leverage(ServiceBase):
    baseUrl = '/api/exchange/leverage'
    
    def positions(self, params = {}):
        NOT_IMPLED: convert to cc style
        return self.coinCheck.request(ServiceBase.METHOD_GET, self.baseUrl + '/positions', params)
