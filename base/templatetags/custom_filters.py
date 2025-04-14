# Create a file called templatetags/custom_filters.py in your app directory
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def subtract(value, arg):
    return float(value) - float(arg)
