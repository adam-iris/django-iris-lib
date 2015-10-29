"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.template import Template, Context

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class TrimTextTest(TestCase):
    """
    Test the {% trimtext %} template tag
    """

    def test(self):
        template_text = """
{% load iris_tags %}{% trimtext %}
    {% if some_condition %}
        {% for item in items %}
{{ item }}
       {% endfor %}
    {% endif %}
{% endtrimtext %}
"""

        expected_output = """
Item 1

Item 2

Item 3
"""

        context = Context({
            'some_condition': True,
            'items': ["Item 1", "Item 2", "Item 3"]
        })
        output = Template(template_text).render(context)

        self.assertEqual(output, expected_output)

