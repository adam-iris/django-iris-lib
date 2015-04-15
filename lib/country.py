from django.utils.translation import ugettext_lazy as _
from django.db import models
import iso3166

# Common country names that depart from the ISO standard
# Note that these shouldn't change the sorting (they are generally just truncated versions of the full name)
COUNTRY_COMMON_NAMES = {
    "BN": _(u"Brunei"),
    "BO": _(u"Bolivia"),
    "IR": _(u"Iran"),
    "KP": _(u"Korea, North"),
    "KR": _(u"Korea, South"),
    "LA": _(u"Laos"),
    "MD": _(u"Moldova"),
    "MK": _(u"Macedonia"),
    "SY": _(u"Syria"),
    "TW": _(u"Taiwan"),
    "TZ": _(u"Tanzania"),
    "VE": _(u"Venezuela"),
    "VN": _(u"Vietnam"),
}


def get_country_name(country_code):
    # Common name if it exists
    if country_code in COUNTRY_COMMON_NAMES:
        return COUNTRY_COMMON_NAMES[country_code]
    # iso3166 country if it exists
    country = iso3166.countries.get(country_code, None)
    if country:
        return _(country.name)
    # Otherwise, return the code itself
    return country_code


# Make a choice list, with US at the top and otherwise sorted by name
COUNTRIES = [("US", get_country_name("US"))] + [
    (country.alpha2, get_country_name(country.alpha2))
    for country in iso3166.countries
    if country.alpha2 != "US"
]


class CountryField(models.CharField):

    description = "A field of countries"

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):

        COUNTRY_HELP_TEXT = " ".join([
            'Country names and codes based on the',
            '<a href="http://en.wikipedia.org/wiki/ISO_3166-1" target="_blank">',
            'ISO 3166 standard</a>.'
        ])

        kwargs.setdefault('max_length', 2)
        kwargs.setdefault('choices', COUNTRIES)
        kwargs.setdefault('help_text', COUNTRY_HELP_TEXT)

        super(CountryField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

# http://south.readthedocs.org/en/latest/tutorial/part4.html#tutorial-part-4
from south.modelsinspector import add_introspection_rules
add_introspection_rules(
    [
        (
            [CountryField], # Class(es) these apply to
            [],             # Positional arguments (not used)
            {},
        ),
    ], [
        "^lib\.fields\.CountryField",
    ]
)
