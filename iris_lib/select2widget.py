from django.conf import settings
from django import forms
import copy
import json
from iris_lib.raw_js_json import RawJsJSONEncoder
from django.utils.safestring import mark_safe
from django.templatetags.static import static


SELECT2_JS = getattr(settings, 'SELECT2_JS',
                     'libs/select2/select2-3.5.1/select2.js')
SELECT2_CSS = getattr(settings, 'SELECT2_CSS',
                      'libs/select2/select2-3.5.1/select2.css')

SELECT2_WIDGET_JS = [
    static('select2/js/resolve_jquery.js'),
    static('select2/js/lookup_override.js'),
    static(SELECT2_JS),
    static('select2/js/select2custom.js'),
]
SELECT2_WIDGET_CSS = [
    static(SELECT2_CSS),
    static('select2/css/select2custom.css'),
]

SELECT2_DEFAULT_ATTRS = getattr(settings, 'SELECT2_DEFAULT_ATTRS', {
    'width': 'auto',
    'min-width': '250px',
    'dropdownAutoWidth': True,
    'selectOnBlur': True,
})


class Select2CustomMixin(object):
    """
    Base widget mixin, this adds a JS block to instantiate the Select2 component on it.
    """

    inline_script = """
        <script>
            $(function() {
                $("#%(id)s").on('select2changed', function(e){
                    var opts = Select2Custom.prepareOpts(%(options)s);
                    $("#%(id)s").select2(opts);
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
            'screen': SELECT2_WIDGET_CSS,
        }


class Select2(Select2CustomMixin, forms.Select):
    """Adds Select2 to Select."""
    pass


class Select2Multiple(Select2CustomMixin, forms.SelectMultiple):
    """Adds Select2 to SelectMultiple."""
    pass


class Select2TextMixin(Select2CustomMixin):
    """Mixin for text-based widget (required for tagging)"""
    pass


class Select2TextInput(Select2TextMixin, forms.TextInput):
    """Adds Select2 to TextInput"""
    pass

