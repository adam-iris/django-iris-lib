from django.utils.translation import ugettext as _
from django.db import models
import stopspam
from django.utils.log import getLogger
from django.views.generic.edit import ModelFormMixin, FormMixin
from django.http.response import HttpResponseRedirect
import textile
import re
from textwrap import dedent
from django.core.exceptions import ValidationError
import crispy_forms
from django.template.loader import render_to_string
from crispy_forms.layout import TEMPLATE_PACK
from crispy_forms.helper import FormHelper

LOGGER = getLogger(__name__)

class FormModelMixin(models.Model):
    """
    Mixin for a model saved from a form submission.  Includes an email address field (to be filled by the user)
    and automatically-filled forms for submission date, IP address and calculated spam score.
    """
    # Threshold for considering a submission to be spam (0-100)
    SPAM_THRESHOLD = 90

    # Email address appears in the public form
    email = models.EmailField(_('Email Address'))
    # Other fields are calculated and should not be visible
    submitted_date = models.DateTimeField(_('Submitted Date'),
        auto_now_add=True)
    ip_address = models.CharField(_('IP Address'),
        max_length=64, blank=True,
        editable=False,
        help_text="IP address of the submitter")
    spam_score = models.IntegerField(_('Spam Score'),
        blank=True, null=True,
        editable=False,
        help_text="0=definitely not spam, 100=definitely spam.")

    @property
    def is_spam(self):
        """ True if the spam score exceeds the threshold """
        return bool(self.spam_score and (self.spam_score > self.SPAM_THRESHOLD))

    def spam_check(self):
        """
        Inverse of is_spam, which is also marked as boolean. This is for use by admin pages, so they will display
        green (True) if the submission is not spam, and red (False) if the submission is spam.
        """
        return not self.is_spam
    spam_check.boolean = True

    class Meta:
        abstract = True

class FormSaveMixin(FormMixin):
    """
    Mixin to save a validated form to an object, with pluggable functionality running before and after.
    """
    def before_save(self):
        """
        Called after the object has been successfully created from a form submission (but not yet saved).
        `self.object` is the (unsaved) objecrt
        """
        pass

    def after_save(self):
        """
        Called after the object has been saved.
        `self.object` is the saved object.
        """
        pass

    def form_valid(self, form):
        """
        Saves the form into `self.object` with hooks for finalizing the object and acting after
        a successful save.
        """
        self.object = form.save(commit=False)
        self.before_save()
        self.object.save()
        # Because form.save(commit=False) skips saving ManyToMany fields, look for the method
        # that gets auto-created and run it if it exists
        if hasattr(form, 'save_m2m'):
            form.save_m2m()
        self.after_save()
        return super(FormSaveMixin,self).form_valid(form)


class SpamCheckMixin(FormSaveMixin):
    """
    Mixin for a class-based view whose model uses FormModelMixin; this provides functions to record
    the request IP address and calculate the spam score based on that and the user email.
    This requires a model object that has `ip_address`, `email` and `spam_score` fields.
    """

    def add_ip_address(self):
        """
        Add the requester IP address to the view's object
        """
        # Forwarded requests may have multiple IP addresses; the first one is the real client IP
        ip_list = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR'))
        self.object.ip_address = ip_list.split(',')[0]

    def spam_check(self):
        """
        Check the requester IP address and email against spam database
        """
        try:
            spam_score = 0
            for spam_field in (self.object.ip_address, self.object.email):
                score = stopspam.confidence(spam_field)
                if score > spam_score:
                    spam_score = score
            self.object.spam_score = int(spam_score)
        except Exception as e:
            LOGGER.error("Failed to run spam check: %s", e)

    def before_save(self):
        """
        Add the IP address and perform a spam check before saving.
        """
        self.add_ip_address()
        self.spam_check()
        super(SpamCheckMixin,self).before_save()

def textile_block(text, **kwargs):
    """
    Helper for making blocks of textile-formatted content.  This is mostly for writing blocks of
    content in a django-crispy-forms Layout definition:

    > HTML(textile_block('''
    >        Here is a paragraph of text with *textile* @markup@.

    >        A new line indented even with the first line generates
    >        a newline in the output, but
    >         indenting an extra character causes textile to ignore the newline.
    >        This can fail when the newline is _inside a formatting block, so you can also use \
    >         a backslash at the end of the previous line_.
    >        '''))

    Text is
    1. Dedented (so it can be a triple-quoted, indented block)
    2. Lines that end with backslash (\) are hard-joined to the next line, because some markup
        can't cross lines
    3. Run through textile
    """
    return textile.textile(re.sub(r'\\\n', ' ', dedent(text)), **kwargs)

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


class Formset(object):
    """
    Renders a formset as though it were a field
    """

    template = "forms/table_inline_formset.html"

    def __init__(self, formset, template=None):
        self.formset = formset
        if template:
            self.template = template

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return render_to_string(self.template, {
            'formset': self.formset
        }, context)


class Subform(object):
    """
    A crispy-forms layout object representing a subform.

    A good use case is gathering user data including institution.  We want the user to pick an institution
    if possible, but they might need to enter data for a new one instead. This layout object allows an institution
    form to be embedded in the user form and optionally shown/processed.

    There are two standard strategies for combining multiple forms:

    One option is to make each form an independent top-level entity.  The main problem here is that they can't
    be mixed at all in rendering, you have to render Form A, then Form B, etc.

    Another option is to build a combination form by copying all the fields from multiple forms into one.  This
    has a few issues:
    - Field names can easily collide
    - Form-level behavior (ie. Form.clean(), or any ModelForm-related behavior) is lost
    - You can't make one of the forms optional while keeping validation on individual form fields -- the only
        way to make a form optional is by making all of its fields optional.  So in the case above, the
        user may not fill in the institution data, but if they do the institution name is required; there's no
        easy way to do this.

    With subforms, one form is owned by another, and the parent form's layout uses this tag to place the subform
    within its own layout.  The parent form can control whether the subform is processed, but the actual
    processing is still owned by the subform.

    Field name collisions should be addressed with form prefixes -- all Django forms support being given a prefix,
    which is used in form field names but is automatically removed before processing.

    The typical pattern for handling subforms is:

    class ParentForm(Form):
        def __init__(self, data=None, instance=None, *args, **kwargs):
            super(ParentForm, self).__init__(data=data, instance=instance, *args, **kwargs)
            # Pass form data but not instance to subform
            self.subform = SubForm(data=data, *args, **kwargs)
        def clean(self):
            if (should_process_subform):
                if not self.subform.is_valid():
                    # Need to add something to self._errors so the parent form is marked as invalid
                    self._errors['subform'] = self.error_class([_('Subform invalid')])
            return super(ParentForm, self).clean()
    """

    template = 'forms/subform.html'

    def __init__(self, subform, template=None):
        self.subform = subform
        if template:
            self.template = template

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        return render_to_string(self.template, {
            'subform': self.subform
        }, context)


class DefaultFormHelper(FormHelper):
    """
    A base form helper class, mainly to define defaults
    """
    form_class = 'form-horizontal'
    label_class = 'col-xs-3'
    field_class = 'col-xs-9'


class PartialFormHelper(DefaultFormHelper):
    """
    A form helper class for partial forms (without <form> tags or CSRF)
    """
    form_tag = False
    disable_csrf = True


class FormHelperMixin(object):
    """
    A mixin for a form class, mostly this just takes care of the plumbing using crispy-forms to lay out
    the form. Using this mixin, a subclass should only need to define create_form_layout().
    """
    form_helper_class = DefaultFormHelper
    _helper = None

    @property
    def helper(self):
        """
        Get the helper, creating it if necessary.  Subclasses should not override this.
        """
        if not self._helper:
            self._helper = self.create_form_helper()
            layout = self.create_form_layout()
            if layout:
                self._helper.layout = layout
        return self._helper

    def create_form_helper(self):
        """
        Create the helper.  Subclasses may override this if they need some special tweaks
        to the helper itself.
        """
        return self.form_helper_class(self)

    def create_form_layout(self):
        """
        Create the layout.  This is what most subclasses should implement.
        @return: a Layout object
        """
        return None
