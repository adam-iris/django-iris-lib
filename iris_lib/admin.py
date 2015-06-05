from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import Widget
import copy
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from iris_lib.select2widget import Select2
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType


def get_change_url(instance):
    """
    Get the URL for the change_view for the given instance
    """
    return reverse('admin:%s_%s_change' % (
        instance._meta.app_label,
        instance._meta.model_name),
        args=(instance.pk,))


def get_add_url(model):
    return reverse('admin:%s_%s_add' % (
        model._meta.app_label,
        model._meta.model_name,
    ))


class LinkedObjectWidgetWrapper(Widget):
    """
    This works like the RelatedFieldWidgetWrapper, which adds the (+) link for admin dropdowns.
    This version prepends a link to the change page for the current value.
    """
    def __init__(self, widget, rel_to, admin_site, *args, **kwargs):
        super(LinkedObjectWidgetWrapper, self).__init__(*args, **kwargs)
        self.widget = widget
        self.rel_to = rel_to
        self.admin_site = admin_site

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.widget = copy.deepcopy(self.widget, memo)
        obj.attrs = self.widget.attrs
        memo[id(self)] = obj
        return obj

    @property
    def media(self):
        return self.widget.media

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        self.attrs = self.widget.build_attrs(extra_attrs=None, **kwargs)
        return self.attrs

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)

    def render(self, name, value, *args, **kwargs):
        html = self.widget.render(name, value, *args, **kwargs)
        if not value:
            return html

        info = (self.rel_to._meta.app_label, self.rel_to._meta.model_name)
        related_url = reverse('admin:%s_%s_change' % info, args=(value,), current_app=self.admin_site.name)
        value_label = value
        for option_value, option_label in self.widget.choices:
            if str(option_value) == str(value):
                value_label = option_label
                break
        output = u'%s <a href="%s">%s</a><br/>%s' % (
            _('Currently:'), related_url, value_label,
            html
        )
        return mark_safe(output)


class LinkedObjectAdminMixin(object):
    """
    Mixin for ModelAdmin to apply LinkedObjectWidgetWrapper
    """

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Use the LinkedObjectWidgetWrapper for dbfields
        """
        formfield = super(LinkedObjectAdminMixin, self).formfield_for_dbfield(db_field, **kwargs)
        if formfield and isinstance(formfield.widget, RelatedFieldWidgetWrapper):
            formfield.widget = LinkedObjectWidgetWrapper(
                formfield.widget, db_field.rel.to, self.admin_site)
        return formfield


class Select2AdminMixin(object):
    """
    Mixin for ModelAdmin that defaults to Select2Widget for all select fields
    """
    select2_fields = None

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Apply the formfield overrides to all choice fields (normally not applied)
        """
        use_select2 = False
        if self.select2_fields:
            use_select2 = (db_field.name in self.select2_fields)
        else:
            use_select2 = (db_field.rel or db_field.choices)
        if use_select2:
            kwargs.setdefault('widget', Select2)
        return super(Select2AdminMixin, self).formfield_for_dbfield(db_field, **kwargs)


class AdminViewContextMixin(object):
    """
    Mixin for ModelAdmin to help generate the context necessary for using admin templates.
    """

    def get_change_url(self, instance):
        """
        Get the URL for the change_view for the given instance
        """
        return reverse('admin:%s_%s_change' % (
            instance._meta.app_label,
            instance._meta.model_name),
            args=(instance.pk,),
            current_app=self.admin_site.name)

    def get_add_url(self):
        return reverse('admin:%s_%s_add' % (
            self.opts.app_label,
            self.opts.model_name),
            current_app=self.admin_site.name)

    def get_base_form_context(self, obj=None, title=None, opts=None):
        if not opts:
            opts = self.opts
        add = bool(obj)
        if not title:
            if add:
                title = _('Add %s') % force_text(opts.verbose_name)
            else:
                title = _('Change %s') % force_text(opts.verbose_name)
        context = {
            'add': add,
            'change': not add,
            'title': title,
            'app_label': opts.app_label,
            'module_name': force_text(opts.verbose_name_plural),
            'opts': opts,
            'media': self.media,
            'is_popup': False,
            'inline_admin_formsets': [],
            'errors': None,
            'preserved_filters': None,
            'has_add_permission': True,
            'has_change_permission': True,
            'has_delete_permission': True,
            'has_file_field': True,
            'has_absolute_url': False,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
        }
        if obj:
            context.update({
                'object': obj,
                'object_id': obj.id,
                'original': obj,
            })
        return context

    def get_change_form_context(self, obj, title=None, opts=None):
        """
        Return a context dict containing most of the pieces that the object change_form template
        uses.  This is to allow the action to render to a template extending change_form.
        """
        return self.get_base_form_context(obj, title=title, opts=opts)

    def get_add_form_context(self, title=None, opts=None):
        """
        Return a context dict containing most of the pieces that the object change_form template
        uses.  This is to allow the action to render to a template extending change_form.
        """
        return self.get_base_form_context(obj=None, title=title, opts=opts)


