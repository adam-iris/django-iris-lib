from django.utils.translation import ugettext as _
from django.db import models
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

    A good use case is picking/adding an institution.  We want the user to pick an institution
    if possible, but they might need to enter data for a new one instead. This layout object allows an institution
    form to be embedded in the user form and optionally shown/processed.

    The typical pattern for handling subforms is:

    class ChildForm(Form):
        # Define the subform

    class ParentForm(Form):
        def __init__(self, data=None, instance=None, *args, **kwargs):
            super(ParentForm, self).__init__(data=data, instance=instance, *args, **kwargs)
            # Pass form data but not instance (which is the Parent object) to subform
            # Also, make sure the subform uses a prefix, to ensure no field name collisions
            self.subform = ChildForm(data=data, prefix='subform', *args, **kwargs)
        def clean(self):
            # Generally the parent form has some input indicating the user filled in the subform
            if (should_process_subform):
                if not self.subform.is_valid():
                    # Need to add something to self._errors so the parent form is marked as invalid
                    self._errors['subform'] = self.error_class([_('Subform invalid')])
            return super(ParentForm, self).clean()
        # Assume we use `FormHelperMixin` to define the crispy-forms layout
        def create_form_layout(self):
            return Layout(
                # Here we put the subform in among a bunch of other fields
                'field1',
                'field2',
                Subform(self.subform),
                'field3'
            )


    RATIONALE:

    There are two standard strategies for combining multiple forms:

    One option is to make each form an independent top-level entity.  The main problem here is that they can't
    be mixed at all in rendering, you have to render Form A, then Form B, etc.

    Another option is to build a combination form by copying all the fields from multiple forms into one.  This
    has a few issues:
    - Field names can easily collide
    - Form-level behavior (ie. Form.clean(), or any ModelForm-related behavior) is lost
    - You can't make one of the forms optional while keeping validation on individual form fields. In the
        case above, for example, the institution data as a whole may be optional, but if it's filled out
        certain elements are required.  This can't be handled with a flat list of fields.

    With subforms, one form is owned by another, and the parent form's layout uses this tag to place the subform
    within its own layout.  The parent form can control whether the subform is processed, but the actual
    processing is still owned by the subform.

    Field name collisions should be addressed with form prefixes -- all Django forms support being given a prefix,
    which is used in form field names but is automatically removed before processing.

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
