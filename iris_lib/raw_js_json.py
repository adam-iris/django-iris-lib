import json
import uuid

#######
# Method for outputting raw Javascript using the JSON framework.
# This is most useful when producing a Javascript object containing functions, eg.
#
# ajax_options = {
#     'success': RawJavaScriptText('function(data) { console.log("Success!"); }')
# }
#
# This works by using a UUID value as a placeholder, and then substituting the
# raw Javascript in at the very end.
#
# See http://stackoverflow.com/questions/13188719
#######


class RawJavaScriptText:
    def __init__(self, jstext):
        self._jstext = jstext
    def get_jstext(self):
        return self._jstext


class RawJsJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        json.JSONEncoder.__init__(self, *args, **kwargs)
        self._replacement_map = {}

    def default(self, o):
        if isinstance(o, RawJavaScriptText):
            key = uuid.uuid4().hex
            self._replacement_map[key] = o.get_jstext()
            return key
        else:
            return json.JSONEncoder.default(self, o)

    def encode(self, o):
        result = json.JSONEncoder.encode(self, o)
        for k, v in self._replacement_map.iteritems():
            result = result.replace('"%s"' % (k,), v)
        return result
