from django.conf import settings
from django import forms
import copy
import json
from lib.raw_js_json import RawJavaScriptText, RawJsJSONEncoder
from django.utils.safestring import mark_safe
from django.templatetags.static import static


SELECT2_JS = getattr(settings, 'SELECT2_JS',
                     'libs/select2/select2-3.5.1/select2.min.js')
SELECT2_CSS = getattr(settings, 'SELECT2_CSS',
                      'libs/select2/select2-3.5.1/select2.css')

SELECT2_WIDGET_JS = [
    static('select2/js/resolve_jquery.js'),
    static('select2/js/lookup_override.js'),
    static(SELECT2_JS),
]

SELECT2_DEFAULT_ATTRS = getattr(settings, 'SELECT2_DEFAULT_ATTRS', {
    'width': 'auto',
    'min-width': '250px',
    'dropdownAutoWidth': True
})


class Select2CustomMixin(object):
    """
    Overrides parts of the base Select2Mixin, to provide better support for things like
    auto_tagging and overrideable widget attributes.
    """

    inline_script = """
        <script>
            $(function() {
                $("#%(id)s").on('select2changed', function(e){
                    $("#%(id)s").select2(%(options)s);
                }).trigger('select2changed');
            });
        </script>
    """

    def __init__(self, select2attrs=None, *args, **kwargs):
        self.select2attrs = copy.copy(SELECT2_DEFAULT_ATTRS)
        if select2attrs:
            self.select2attrs.update(select2attrs)
        super(Select2CustomMixin, self).__init__(*args, **kwargs)

    def render(self, *args, **kwargs):
        """
        Extend base class's `render` method by appending
        javascript inline text to html output.
        """
        output = super(Select2CustomMixin, self).render(*args, **kwargs)
        id_ = kwargs['attrs']['id']
        options = json.dumps(self.select2attrs, cls=RawJsJSONEncoder)
        output += self.inline_script % {
            'id': id_,
            'options': options,
        }
        return mark_safe(output)

    class Media:
        js = SELECT2_WIDGET_JS
        css = {
            'screen': [
                static(SELECT2_CSS)
            ],
        }


class Select2(Select2CustomMixin, forms.Select):
    """Adds Select2 to Select."""
    pass


class Select2Multiple(Select2CustomMixin, forms.SelectMultiple):
    """Adds Select2 to SelectMultiple."""
    pass


class Select2TextMixin(Select2CustomMixin):
    """Mixin for text-based widget (required for tagging)"""
    def __init__(self, select2attrs=None, auto_tag=False, *args, **kwargs):
        super(Select2TextMixin, self).__init__(select2attrs, *args, **kwargs)
        if auto_tag:
            if 'createSearchChoice' not in self.select2attrs:
                self.select2attrs['createSearchChoice'] = RawJavaScriptText("""
                    function(term, results) {
                        console.log("createSearchChoice: " + term + ", " + results);
                        if (!results || !results.length) {
                            return { 'id': term, 'text': term, 'tag': true };
                        }
                    }
                """)
            if 'nextSearchTerm' not in self.select2attrs:
                self.select2attrs['nextSearchTerm'] = RawJavaScriptText("""
                    function (obj, term) {
                        console.log("nextSearchTerm: " + obj + ", " + term);
                        if (obj) {
                            return obj.text;
                        } else {
                            return term;
                        }
                    }
                """)
        if ('data' in self.select2attrs and
                'createSearchChoice' in self.select2attrs and
                'initSelection' not in self.select2attrs):
            self.inline_script = """
                <script>
                    $(function(){
                        var options = %(options)s;
                        options.initSelection = function(element, callback) {
                            // Look for current value as an id, otherwise create a search choice
                            var id = $(element).val();
                            var match = null;
                            var data = options.data.results || options.data;
                            if (data && data.length) {
                                match = $.grep(data, function(item) {
                                    return (id == item.id);
                                })[0];
                            }
                            console.log("initSelection: " + id + ", " + match);
                            if (!match) {
                                match = options.createSearchChoice(id);
                            }
                            if ($.isFunction(callback)) {
                                callback(match);
                            }
                        };
                        $("#%(id)s").select2(options);
                    });
                </script>
            """


class Select2TextInput(Select2TextMixin, forms.TextInput):
    """Adds Select2 to TextInput"""
    pass
