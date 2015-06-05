import requests

###
# Webservice request library
#
# Example:
#
# class MyRequest(BaseRequest):
#     """
#     Define a particular webservice request
#     """
#     # These are the keys and types that can be passed into the query
#     param_types = {
#         # A generic string parameter
#         'name': WSParam(),
#         # A date, will be put in the query as ISO format
#         'birthday': WSDateParam(),
#     }
#     # Base query url
#     url = 'http://hostname/path/to/query'
# 
# req = MyRequest(name='Foo', birthday=datetime.date(1983,5,12))
# 
# response = """
# # id | name | message
# 1|Foo|Hi there
# 2|Bar|Yarr
# """
# 
# for row in req.get():
#     name = row['name']
#     message = row['message']
#     print '%s says "%s"' % (name, message)
# 
# prints = """
# Foo says "Hi there"
# Bar says "Yarr"
# """

class WSParam(object):
    """
    Defines a web service query parameter.  This allows the service API to take parameter
    values as Python objects, and convert them to the proper string form for the service.
    """
    def __init__(self, param_name=None, default=None):
        self.param_name = param_name
        self.default = default
    
    def to_param(self, value):
        return str(value)
    
class WSDateParam(WSParam):
    """
    A date parameter.
    """
    def to_param(self, value):
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        elif isinstance(value, str):
            return value
        else:
            raise ValueError("%s is not a date" % (value,))

class WSBinaryParam(WSParam):
    """
    A binary parameter that is passed in a query as "yes" or "no".
    """
    def to_param(self, value):
        return "yes" if value else "no"


class BaseRequest(object):
    """
    Base class for a web service request.
    """
    
    # The subclass must define this.  It is a dict of parameter names to WSParam types.
    param_types = None
    url = None
    
    def __init__(self, **params):
        if not self.param_types:
            raise Exception("This class must define some param_types")
        self.params = self.get_default_params()
        self.headers = self.get_default_headers()
        if params:
            self.set_params(**params)
    
    def set_params(self, **kwargs):
        """
        Set the query parameters
        """
        for k,v in kwargs.items():
            if k not in self.param_types:
                raise Exception("Unknown parameter %s" % k)
            self.params[k] = self.param_types[k].to_param(v)
    
    def get_params(self):
        return self.params
    
    def get_headers(self):
        return self.headers
    
    def get_default_params(self):
        """
        Define default query parameters.  If any of the parameters in self.param_types
        has a default value, that will be included.  Otherwise, the subclass may 
        extend this to add defaults.
        """
        params = {}
        for k,v in self.param_types.items():
            if v.default:
                params[k] = v.default
        return params
    
    def get_default_headers(self):
        """
        Subclass may override this to define default request headers
        """
        return {}
    
    def get_request_kwargs(self):
        """
        Return a dict of kwargs to pass to requests.get()
        """
        return dict(
            params=self.get_params(),
            headers=self.get_headers(),
            stream=True,
        )
    
    def get_url(self):
        return self.url
    
    def get(self):
        """
        Execute an HTTP GET.  The returned value is an iterable that gives
        each value in the response.
        """
        r = requests.get(self.get_url(), **self.get_request_kwargs())
        r.raise_for_status()
        return self.parse(r)

    def parse(self, response):
        """
        Parse the query response.  By default, this parses as FDSN text/csv format.
        This should yield each value in the response.
        """
        keys = None
        for line in response.iter_lines():
            if not keys:
                # First line of response is treated as the field names
                keys = [s.replace('#','').strip() for s in line.split('|')]
            else:
                # Split line, turn into a dict, and create an entity value for it
                values = [s.strip() for s in line.split('|')]
                entity = self.entity(dict(zip(keys, values)))
                # Only yield the entity if it's not None, this allows skipping/filtering of data
                if entity != None:
                    yield entity

    def entity(self, obj_dict):
        """
        Given a key/value dict of returned data, return an object to pass back.  If this
        returns None, that data will be skipped.
        """
        return obj_dict

