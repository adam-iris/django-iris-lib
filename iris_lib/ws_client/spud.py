import json
from iris_lib.ws_client import ws_request

class SpudEventProductsRequest(ws_request.BaseRequest):

    param_types = dict(
        eventid = ws_request.WSParam(),
        output = ws_request.WSParam(default='json')
    )
    url = 'http://www.iris.edu/spudservice/item'
    
    def parse(self, response):
        return json.loads(response.text)
