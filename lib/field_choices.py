######
#
# This is sort of like an enum, but geared toward use in a Django field.
#
# >>> class MyChoices(Choices):
# ...    VALUE1 = Choice("First Value")
# ...    VALUE2 = Choice("Second Value")
#
# >>> # By default, the field value is the attribute name
# >>> MyChoices.VALUE1
# 'VALUE1'
#
# >>> # You can get the label for any choice value
# >>> MyChoices.get_label(MyChoices.VALUE1)
# 'First Value'
#
# >>> # The choices can be returned in a format suitable for a Model field
# >>> MyChoices.get_choices()
# [('VALUE1', 'First Value'), ('VALUE2', 'Second Value')]
#
######

class Choice(object):
    """
    A single option in a Choices type.
    """
    # Global counter allows choices to be kept in order of definition
    _counter = 0

    def __init__(self, label=None, value=None):
        self.label = label
        self.value = value
        self._counter = Choice._counter
        Choice._counter += 1


class ChoicesMeta(type):
    """
    Metaclass for a Choices type.
    """
    def __new__(cls, name, bases, attrs):
        labels = {}
        # The choices are in the `attrs` dict; sort them by definition order
        ordered_choices = sorted(
            [(attr, choice) for attr, choice in attrs.iteritems() if isinstance(choice, Choice)],
            cmp=lambda x, y: cmp(x[1]._counter, y[1]._counter)
        )
        for attr, choice in ordered_choices:
            # Default value is the attribute name
            if choice.value is None:
                choice.value = attr
            # Default label is a title-ized attribute name
            if choice.label is None:
                choice.label = _(str(attr).replace('_', ' ').title())
            value = choice.value
            # Set the actual class attributes to reflect the choice value
            attrs[attr] = attrs[value] = value
            labels[attr] = labels[value] = choice.label
        # Add the choices as an ordered list, and a label lookup dict, to the class attributes
        attrs['_choices'] = ordered_choices
        attrs['_labels'] = labels
        return type.__new__(cls, name, bases, attrs)


class Choices(object):
    """
    Base class for a set of choices.

    >>> class MyChoices(Choices):
    ...    VALUE1 = Choice("First Value")
    ...    VALUE2 = Choice("Second Value")

    """
    __metaclass__ = ChoicesMeta

    @classmethod
    def get_choices(cls):
        choices = []
        for attr, choice in cls._choices:
            value = getattr(cls, attr)
            label = choice.label
            choices.append((value, label))
        return choices

    @classmethod
    def get_label(cls, attr):
        return cls._labels.get(attr)

