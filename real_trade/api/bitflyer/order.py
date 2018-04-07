from servicebase import ServiceBase

class Order(ServiceBase):
    baseUrl = '/api/exchange/orders'

    def min_create_order_btc(self):
        return 0.005

    def create(self, params = {}):
        NOT_IMPLED: convert to cc style
        print("create", params)
        return self.coinCheck.request(ServiceBase.METHOD_POST, self.baseUrl, params)

    def cancel(self, params = {}):
        defaults = {
            'id': ""
        }
        defaults.update(params)
        params = defaults.copy()
        return self.coinCheck.request(ServiceBase.METHOD_DELETE, self.baseUrl + '/' + str(params['id']), params)
    
    def opens(self, params = {}):
        return self.coinCheck.request(ServiceBase.METHOD_GET, self.baseUrl + '/opens', params)
    
    def transactions(self, params = {}):
        return self.coinCheck.request(ServiceBase.METHOD_GET, self.baseUrl + '/transactions', params)
