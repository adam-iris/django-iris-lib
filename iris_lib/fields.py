from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
from email.utils import formataddr


class DOIValidator(RegexValidator):
    regex = r'doi:\d+\.\d+/\S+\w'
    message = _('Invalid DOI. DOIs must be in the form "doi:DD.DDDD/XXXX"')
    code = 'invalid'
validate_doi = DOIValidator()


def validate_true(value):
    """
    Validates that the value is true.  Useful for BooleanField that must be checked
    (eg. acceptance of licensing terms)
    """
    if not value:
        raise ValidationError(_('This field is required'))


######
# Helpers to create a required boolean form input with radio buttons, eg.
# ( ) Yes  ( ) No
# You need to distinguish between False (user chose No) and None (user didn't choose anything)
# The way to make this work is:
#
# class MyForm(forms.Form):
#   req_bool = forms.TypedChoiceField(choices=YES_NO_CHOICES, coerce=YES_NO_COERCE, label=_("Yes or no?"))
#
# Assuming you're using django-crispy-forms, in the Layout use:
#   InlineRadios('req_bool')
#
# The input will raise an error if nothing is selected, and yield a True/False value otherwise
######

YES_NO_CHOICES = (
    ("Y", _('Yes')),
    ("N", _('No'))
)

def YES_NO_COERCE(val):
    """
    Coerce a yes/no choice value into a boolean
    """
    return val == "Y"

def validate_picked(value):
    """
    When a BooleanField has choices, validates that one of them was picked.
    """
    if value == None:
        raise ValidationError(_('This field is required'))


#####
# Prettified user choices, use these for form fields giving user choices
#####

class PrettifiedUserChoiceMixin(object):
    def label_from_instance(self, obj):
        return formataddr((obj.get_full_name(), obj.email))


class UserModelChoiceField(PrettifiedUserChoiceMixin, ModelChoiceField):
    pass


class UserModelMultipleChoiceField(PrettifiedUserChoiceMixin, ModelMultipleChoiceField):
    pass
