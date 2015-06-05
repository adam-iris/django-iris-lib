from django import template

register = template.Library()

@register.filter('widget_fieldtype')
def widget_fieldtype(field):
    return field.field.widget.__class__.__name__
