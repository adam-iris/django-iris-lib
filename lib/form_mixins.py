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
        `self.object` is the (unsaved) object
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
        # Because form.save(commit=False) doesn't save ManyToMany fields, we need to do it manually.
        # If there are M2M fields, the form will have a `save_m2m` method that can be called to do it.
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
        # This is disabled because it doesn't actually work very well
        # try:
        #     spam_score = 0
        #     for spam_field in (self.object.ip_address, self.object.email):
        #         score = stopspam.confidence(spam_field)
        #         if score > spam_score:
        #             spam_score = score
        #     self.object.spam_score = int(spam_score)
        # except Exception as e:
        #     LOGGER.error("Failed to run spam check: %s", e)

    def before_save(self):
        """
        Add the IP address and perform a spam check before saving.
        """
        self.add_ip_address()
        self.spam_check()
        super(SpamCheckMixin,self).before_save()

